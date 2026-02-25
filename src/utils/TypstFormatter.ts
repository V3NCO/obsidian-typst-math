// Trim and normalise a Typst math string for insertion into the document.
// Unlike LaTeX, Typst does not yet have a dedicated prettier plugin,
// so we just return the trimmed string as-is.
export async function formatTypst(typst_string: string): Promise<string> {
    return typst_string.trim();
}
