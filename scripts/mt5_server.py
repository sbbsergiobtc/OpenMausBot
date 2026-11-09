import json
import logging
import sys
from bottle import Bottle, request, response, run
import MetaTrader5 as mt5

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger('mt5_server')

app = Bottle()

import time

_ACCOUNTS_CACHE = {}
_ACCOUNTS_CACHE_TIME = {}

def get_cached_account(account_target, max_age_sec=120):
    now = time.time()
    cfg = get_account_cfg(account_target)
    if not cfg:
        return None
    login = int(cfg['login'])

    curr = mt5.account_info()
    if curr is not None and curr.login == login:
        _ACCOUNTS_CACHE[login] = curr._asdict()
        _ACCOUNTS_CACHE_TIME[login] = now
        return _ACCOUNTS_CACHE[login]

    if login in _ACCOUNTS_CACHE and (now - _ACCOUNTS_CACHE_TIME.get(login, 0)) < max_age_sec:
        return _ACCOUNTS_CACHE[login]

    if ensure_account(account_target):
        acc = mt5.account_info()
        if acc:
            _ACCOUNTS_CACHE[login] = acc._asdict()
            _ACCOUNTS_CACHE_TIME[login] = now
            return _ACCOUNTS_CACHE[login]
    return _ACCOUNTS_CACHE.get(login)


def get_brokers_cfg():
    try:
        with open('Z:/root/AlgrokQuant/config/brokers.json') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f'Could not load brokers.json: {e}')
        return {}

def get_account_cfg(account_target=None):
    brokers = get_brokers_cfg()
    if not account_target:
        return brokers.get('icmarkets_mt5')
    tgt = str(account_target).strip().upper()
    if tgt in ['53138338', 'CAPITAL_PROPIO', 'RETAIL', '1000', 'CAPITAL_PROPIO_1K']:
        return brokers.get('icmarkets_mt5')
    if tgt in ['53138341', 'CFD_50K', 'PROP_FIRM_CFD', 'CFD', 'PROP_CFD']:
        return brokers.get('icmarkets_mt5_cfd_50k')
    if tgt in ['53138343', 'PROP_FIRM', 'FUTURES', 'PROP', '50000', '50K', 'PROP_FIRM_FUTURES', 'PROP_FUTURES']:
        return brokers.get('icmarkets_mt5_futures_50k')
    return brokers.get('icmarkets_mt5')

def ensure_connected():
    if mt5.terminal_info() is None or not mt5.terminal_info().connected:
        cfg = get_account_cfg('CAPITAL_PROPIO')
        logger.info('Initializing MT5 connection...')
        mt5.initialize(
            path='C:/ICMarketsMT5/terminal64.exe',
            login=int(cfg['login']),
            password=cfg['password'],
            server=cfg.get('server', 'ICMarketsSC-Demo'),
            portable=True
        )
        mt5.login(int(cfg['login']), password=cfg['password'], server=cfg.get('server', 'ICMarketsSC-Demo'))

def ensure_account(account_target=None):
    ensure_connected()
    if not account_target:
        return True
    cfg = get_account_cfg(account_target)
    if not cfg:
        return False
    target_login = int(cfg['login'])
    curr = mt5.account_info()
    if curr is not None and curr.login == target_login:
        return True
    logger.info(f"Switching MT5 active login to {target_login} ({cfg.get('desk', '')})...")
    res = mt5.login(target_login, password=cfg['password'], server=cfg.get('server', 'ICMarketsSC-Demo'))
    if not res:
        err = mt5.last_error()
        logger.error(f"Failed switching to {target_login}: {err}")
        return False
    logger.info(f"Switched active login to {target_login} OK")
    return True

@app.hook('before_request')
def setup_cors():
    response.content_type = 'application/json'

@app.route('/health', method='GET')
def health():
    try:
        ensure_connected()
        acc = mt5.account_info()
        if acc is None:
            return {'status': 'error', 'message': 'Account not loaded', 'error': mt5.last_error()}
        return {
            'status': 'ok',
            'login': acc.login,
            'server': acc.server,
            'name': acc.name,
            'balance': acc.balance,
            'equity': acc.equity,
            'currency': acc.currency,
            'leverage': acc.leverage,
            'trade_allowed': acc.trade_allowed
        }
    except Exception as e:
        logger.exception('Health check failed')
        return {'status': 'error', 'message': str(e)}

@app.route('/login', method='POST')
def switch_account():
    data = request.json or {}
    login = int(data.get('login'))
    password = str(data.get('password'))
    server = str(data.get('server', 'ICMarketsSC-Demo'))
    logger.info(f'Switching MT5 login to {login} on {server}...')
    res = mt5.login(login, password=password, server=server)
    if not res:
        err = mt5.last_error()
        logger.error(f'Login to {login} failed: {err}')
        return {'status': 'error', 'error': err}
    acc = mt5.account_info()
    logger.info(f'Switched successfully to {login}! Balance: {acc.balance}')
    return {'status': 'ok', 'account': acc._asdict()}

@app.route('/account', method='GET')
def get_account():
    ensure_connected()
    target = request.query.get('account') or request.query.get('branch')
    if target:
        ensure_account(target)
    acc = mt5.account_info()
    if acc is None:
        return {'status': 'error', 'error': mt5.last_error()}
    return {'status': 'ok', 'account': acc._asdict()}

@app.route('/accounts_summary', method='GET')
def get_accounts_summary():
    ensure_connected()
    force_refresh = request.query.get('refresh', '').lower() in ['1', 'true']
    max_age = 0 if force_refresh else 120
    summary = {
        'status': 'ok',
        'capital_propio': get_cached_account('CAPITAL_PROPIO', max_age_sec=max_age),
        'prop_firm_cfd': get_cached_account('PROP_FIRM_CFD', max_age_sec=max_age),
        'prop_firm_futures': get_cached_account('PROP_FIRM_FUTURES', max_age_sec=max_age),
    }
    summary['prop_firm'] = summary.get('prop_firm_cfd') or summary.get('prop_firm_futures')
    curr = mt5.account_info()
    summary['current_login'] = curr.login if curr else None
    return summary

@app.route('/symbol_info', method='GET')
def get_symbol_info():
    ensure_connected()
    sym = request.query.get('symbol')
    if not sym:
        return {'status': 'error', 'message': 'symbol required'}
    mt5.symbol_select(sym, True)
    info = mt5.symbol_info(sym)
    if info is None:
        return {'status': 'error', 'message': f'Symbol {sym} not found', 'error': mt5.last_error()}
    return {'status': 'ok', 'symbol': info._asdict()}

@app.route('/tick', method='GET')
def get_tick():
    ensure_connected()
    sym = request.query.get('symbol')
    if not sym:
        return {'status': 'error', 'message': 'symbol required'}
    tick = mt5.symbol_info_tick(sym)
    if tick is None:
        return {'status': 'error', 'message': f'Tick for {sym} not found', 'error': mt5.last_error()}
    return {'status': 'ok', 'tick': tick._asdict()}

@app.route('/positions', method='GET')
def get_positions():
    ensure_connected()
    target = request.query.get('account') or request.query.get('branch')
    if target:
        ensure_account(target)
    sym = request.query.get('symbol')
    positions = mt5.positions_get(symbol=sym) if sym else mt5.positions_get()
    if positions is None:
        return {'status': 'ok', 'positions': []}
    return {'status': 'ok', 'positions': [p._asdict() for p in positions]}

@app.route('/orders', method='GET')
def get_orders():
    ensure_connected()
    target = request.query.get('account') or request.query.get('branch')
    if target:
        ensure_account(target)
    sym = request.query.get('symbol')
    orders = mt5.orders_get(symbol=sym) if sym else mt5.orders_get()
    if orders is None:
        return {'status': 'ok', 'orders': []}
    return {'status': 'ok', 'orders': [o._asdict() for o in orders]}

def resolve_filling_type(sym_name):
    info = mt5.symbol_info(sym_name)
    if info is None:
        return mt5.ORDER_FILLING_IOC
    modes = info.filling_mode
    if modes & 1:  # FOK
        return mt5.ORDER_FILLING_FOK
    elif modes & 2:  # IOC
        return mt5.ORDER_FILLING_IOC
    return mt5.ORDER_FILLING_RETURN

@app.route('/order', method='POST')
def send_order():
    ensure_connected()
    data = request.json or {}
    target = data.get('account') or data.get('branch')
    if target:
        if not ensure_account(target):
            return {'status': 'error', 'message': f'Failed switching to target account: {target}'}
    
    sym = data.get('symbol')
    if not sym:
        return {'status': 'error', 'message': 'symbol required'}
    
    mt5.symbol_select(sym, True)
    tick = mt5.symbol_info_tick(sym)
    if not tick:
        return {'status': 'error', 'message': f'Could not get tick for {sym}'}
        
    order_type_str = data.get('type', 'BUY').upper()
    if order_type_str == 'BUY':
        order_type = mt5.ORDER_TYPE_BUY
        price = tick.ask if 'price' not in data else float(data['price'])
    elif order_type_str == 'SELL':
        order_type = mt5.ORDER_TYPE_SELL
        price = tick.bid if 'price' not in data else float(data['price'])
    else:
        return {'status': 'error', 'message': f'Unsupported order type: {order_type_str}'}

    volume = float(data.get('volume', 0.01))
    sl = float(data.get('sl', 0.0))
    tp = float(data.get('tp', 0.0))
    deviation = int(data.get('deviation', 20))
    magic = int(data.get('magic', 20261028))
    comment = str(data.get('comment', 'AlgrokQuant MT5'))
    
    filling = data.get('type_filling')
    if filling is None:
        filling = resolve_filling_type(sym)

    req = {
        'action': mt5.TRADE_ACTION_DEAL,
        'symbol': sym,
        'volume': volume,
        'type': order_type,
        'price': price,
        'sl': sl,
        'tp': tp,
        'deviation': deviation,
        'magic': magic,
        'comment': comment,
        'type_time': mt5.ORDER_TIME_GTC,
        'type_filling': filling
    }

    logger.info(f'Sending order request: {req}')
    res = mt5.order_send(req)
    if res is None:
        return {'status': 'error', 'message': 'order_send returned None', 'error': mt5.last_error()}
    
    res_dict = res._asdict()
    if res.retcode != mt5.TRADE_RETCODE_DONE:
        return {'status': 'failed', 'retcode': res.retcode, 'comment': res.comment, 'result': res_dict}
    
    return {'status': 'ok', 'retcode': res.retcode, 'order': res.order, 'deal': res.deal, 'result': res_dict}

@app.route('/close', method='POST')
def close_position():
    ensure_connected()
    data = request.json or {}
    target = data.get('account') or data.get('branch')
    if target:
        ensure_account(target)

    ticket = data.get('ticket')
    if not ticket:
        return {'status': 'error', 'message': 'ticket required'}
        
    positions = mt5.positions_get(ticket=int(ticket))
    if not positions:
        return {'status': 'error', 'message': f'Position {ticket} not found'}
    pos = positions[0]
    
    sym = pos.symbol
    tick = mt5.symbol_info_tick(sym)
    if not tick:
        return {'status': 'error', 'message': f'Could not get tick for {sym}'}
        
    if pos.type == mt5.ORDER_TYPE_BUY:
        close_type = mt5.ORDER_TYPE_SELL
        price = tick.bid
    else:
        close_type = mt5.ORDER_TYPE_BUY
        price = tick.ask
        
    volume = float(data.get('volume', pos.volume))
    deviation = int(data.get('deviation', 20))
    filling = data.get('type_filling')
    if filling is None:
        filling = resolve_filling_type(sym)

    req = {
        'action': mt5.TRADE_ACTION_DEAL,
        'symbol': sym,
        'volume': volume,
        'type': close_type,
        'position': pos.ticket,
        'price': price,
        'deviation': deviation,
        'magic': pos.magic,
        'comment': 'AlgrokQuant Close',
        'type_time': mt5.ORDER_TIME_GTC,
        'type_filling': filling
    }
    
    res = mt5.order_send(req)
    if res is None:
        return {'status': 'error', 'message': 'order_send returned None', 'error': mt5.last_error()}
    res_dict = res._asdict()
    if res.retcode != mt5.TRADE_RETCODE_DONE:
        return {'status': 'failed', 'retcode': res.retcode, 'comment': res.comment, 'result': res_dict}
    return {'status': 'ok', 'retcode': res.retcode, 'order': res.order, 'deal': res.deal, 'result': res_dict}

if __name__ == '__main__':
    logger.info('Initializing MT5 connection on startup...')
    ensure_connected()
    acc = mt5.account_info()
    if acc:
        logger.info(f'MT5 initialized successfully! Account: {acc.login}, Balance: {acc.balance} {acc.currency}')
    else:
        logger.warning(f'MT5 initialization warning: {mt5.last_error()}')
    run(app, host='127.0.0.1', port=8001, quiet=False)
