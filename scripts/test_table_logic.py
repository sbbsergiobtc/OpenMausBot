# Test script to verify table permutation logic

default_headers = ["ID", "Activo", "ROI", "Drawdown", "Acciones"]
# Suppose user reordered headers: moved "ROI" (index 2) to pos 0
# and "Drawdown" (index 3) to pos 1
custom_headers = ["ROI", "Drawdown", "ID", "Activo", "Acciones"]

# Row from server in default order:
server_row = ["STRAT-001", "NDX_1h", "+45.2%", "-3.1%", "VER"]

# Mapping: for each position in custom_headers, which index in default_headers does it correspond to?
mapping = [default_headers.index(k) for k in custom_headers]
print("Mapping:", mapping)

# Permuted row:
permuted_row = [server_row[i] for i in mapping]
print("Permuted row:", permuted_row)
assert permuted_row == ["+45.2%", "-3.1%", "STRAT-001", "NDX_1h", "VER"]
print("Permutation test passed!")
