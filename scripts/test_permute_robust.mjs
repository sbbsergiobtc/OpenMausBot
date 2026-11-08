// Test robust permutation logic with Map lookup by key

const originalKeys = ['col_0', 'col_1', 'col_2', 'col_3'];

function permute(currentCells, targetOrder) {
  // ensure keys
  currentCells.forEach((c, i) => {
    if (!c.dataset.colKey) c.dataset.colKey = originalKeys[i];
  });
  const map = new Map();
  currentCells.forEach(c => map.set(c.dataset.colKey, c));
  return targetOrder.map(k => map.get(k));
}

// Initial row:
let row = [
  { text: 'A', dataset: {} },
  { text: 'B', dataset: {} },
  { text: 'C', dataset: {} },
  { text: 'D', dataset: {} },
];

// Reorder 1: user moves C (col_2) to position 0
let order1 = ['col_2', 'col_0', 'col_1', 'col_3'];
row = permute(row, order1);
console.log("After reorder 1:", row.map(c => c.text));
console.assert(row.map(c => c.text).join('') === 'CABD');

// Reorder 2: user moves D (col_3) to position 1
let order2 = ['col_2', 'col_3', 'col_0', 'col_1'];
row = permute(row, order2);
console.log("After reorder 2:", row.map(c => c.text));
console.assert(row.map(c => c.text).join('') === 'CDAB');

// Reorder 3: reset to original order
let order3 = ['col_0', 'col_1', 'col_2', 'col_3'];
row = permute(row, order3);
console.log("After reset:", row.map(c => c.text));
console.assert(row.map(c => c.text).join('') === 'ABCD');

console.log("All permutation tests passed cleanly!");
