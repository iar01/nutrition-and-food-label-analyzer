/** GS1 checksum: the same rule as the Python validator from Phase 2. */
export function isValidGs1(code: string): boolean {
  if (!/^(\d{8}|\d{12,14})$/.test(code)) return false;
  const digits = code.split('').map(Number);
  const check = digits.pop() as number;
  const total = digits.reverse().reduce((sum, digit, i) => sum + digit * (i % 2 === 0 ? 3 : 1), 0);
  return (10 - (total % 10)) % 10 === check;
}

export function looksLikeBarcode(value: string): boolean {
  return /^\d{8,14}$/.test(value);
}
