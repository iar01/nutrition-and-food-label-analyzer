def key_prefix(code: str) -> str:
    """Folder prefix of a barcode in the images bucket.

    Rule as I understand it (we verify it in Step 7.3):
    - barcodes with more than 8 digits: zero-pad to 13, then split 3/3/3/rest
    - barcodes with 8 digits or fewer: the folder is just the barcode
    """
    if not code.isdigit():
        raise ValueError(f"not a numeric barcode: {code!r}")
    if len(code) > 8:
        c = code.zfill(13)
        return f"data/{c[0:3]}/{c[3:6]}/{c[6:9]}/{c[9:]}/"
    return f"data/{code}/"


def choose_key(keys: list[str]) -> str | None:
    """Pick ONE 400px image key for a product: front image first, else the lowest numbered one."""
    names = {k: k.rsplit("/", 1)[-1] for k in keys}
    fronts = sorted(k for k, n in names.items() if n.startswith("front_"))
    english = [k for k in fronts if names[k].startswith("front_en.")]
    if english:
        return english[0]
    if fronts:
        return fronts[0]
    numeric = sorted((int(n.split(".")[0]), k) for k, n in names.items() if n.split(".")[0].isdigit())
    return numeric[0][1] if numeric else None