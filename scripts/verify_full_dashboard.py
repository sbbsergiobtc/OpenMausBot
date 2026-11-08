import urllib.request
import json
import sys

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

base = "http://169.58.230.132:8080"
print(f"=== FULL AUDIT OF DASHBOARD & APIS ON VPS ({base}) ===")

# 1. HTML index
print("\n--- 1. Testing GET / ---")
try:
    req = urllib.request.Request(f"{base}/", headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=10) as resp:
        code = resp.getcode()
        body = resp.read().decode('utf-8')
        print(f"HTTP Status: {code}")
        print(f"Body length: {len(body)} bytes")
        
        # Verify key elements
        checks = [
            'q-learning-orchestrator-panel',
            'ql-triple-book-cards',
            'ql-matrix-tbody',
            'fetchQLearningMatrixData',
            'guard-chip-green',
            'guard-chip-amber',
            'guard-chip-red',
            'guard-chip-ready',
            'robust_kurtosis',
            'wr_cushion_pct',
            'meseta_parametrica_pct'
        ]
        for c in checks:
            present = c in body
            print(f"  [CHECK] '{c}': {'FOUND OK' if present else 'MISSING'}")
except Exception as e:
    print(f"Error testing /: {e}")

# 2. GET /api/q_learning_matrix
print("\n--- 2. Testing GET /api/q_learning_matrix ---")
try:
    req = urllib.request.Request(f"{base}/api/q_learning_matrix", headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=10) as resp:
        code = resp.getcode()
        data = json.loads(resp.read().decode('utf-8'))
        print(f"HTTP Status: {code}")
        print(f"Updated at: {data.get('updated_at_utc')}")
        print(f"Architecture: {data.get('architecture', {}).get('algorithm')}")
        print(f"40% Consistency Clamp: {data.get('architecture', {}).get('prop_firm_40pct_consistency_clamp')}")
        
        pf = data.get('policies', {}).get('PROP_FIRM', {})
        print(f"PROP_FIRM readable_10x3_green rows: {len(pf.get('readable_10x3_green', []))}")
        print(f"PROP_FIRM readable_10x3_amber rows: {len(pf.get('readable_10x3_amber', []))}")
        print(f"PROP_FIRM OOS Benchmark Book C ROI: +{pf.get('oos_triple_book_benchmark', {}).get('book_c_qlearning', {}).get('net_roi_pct')}%")
        print(f"PROP_FIRM OOS Benchmark Book C Calmar: {pf.get('oos_triple_book_benchmark', {}).get('book_c_qlearning', {}).get('calmar_eod_ratio')}")
        print(f"PROP_FIRM OOS Clamps 40% TP: {pf.get('oos_triple_book_benchmark', {}).get('book_c_qlearning', {}).get('consistency_40pct_early_clamps')}")

        cp = data.get('policies', {}).get('CAPITAL_PROPIO', {})
        print(f"CAPITAL_PROPIO readable_10x3_green rows: {len(cp.get('readable_10x3_green', []))}")
        print(f"CAPITAL_PROPIO OOS Benchmark Book C ROI: +{cp.get('oos_triple_book_benchmark', {}).get('book_c_qlearning', {}).get('net_roi_pct')}%")
except Exception as e:
    print(f"Error testing /api/q_learning_matrix: {e}")

# 3. GET /api/summary
print("\n--- 3. Testing GET /api/summary ---")
try:
    req = urllib.request.Request(f"{base}/api/summary", headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=10) as resp:
        code = resp.getcode()
        sdata = json.loads(resp.read().decode('utf-8'))
        print(f"HTTP Status: {code}")
        ig = sdata.get('kpis', {}).get('incubation_guardian', {})
        print(f"Incubation Guardian Traffic Lights: GREEN={ig.get('green_count')}, AMBER={ig.get('amber_count')}, RED={ig.get('red_count')}")
        print(f"Ready for Real Account: {ig.get('ready_for_real_account_count')}")
except Exception as e:
    print(f"Error testing /api/summary: {e}")

# 4. GET /api/strategies
print("\n--- 4. Testing GET /api/strategies ---")
try:
    req = urllib.request.Request(f"{base}/api/strategies", headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=10) as resp:
        code = resp.getcode()
        strats = json.loads(resp.read().decode('utf-8'))
        print(f"HTTP Status: {code}")
        print(f"Strategies count: {len(strats)}")
        if strats:
            s0 = strats[0]
            print(f"Sample Strategy ID: {s0.get('id')}")
            print(f"  regime_gate: {s0.get('regime_gate')}")
            print(f"  robust_kurtosis: {s0.get('robust_kurtosis')}")
            print(f"  wr_cushion_pct: {s0.get('wr_cushion_pct')}%")
            print(f"  meseta_parametrica_pct: {s0.get('meseta_parametrica_pct')}%")
            print(f"  incubation_guardian: {s0.get('incubation_guardian')}")
except Exception as e:
    print(f"Error testing /api/strategies: {e}")

print("\n=== AUDIT COMPLETE ===")
