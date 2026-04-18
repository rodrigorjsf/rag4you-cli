---
applyTo: "**/locales/*.yaml,**/locales/*.yml,**/locales/*.json"
---

# Locale Parity

- When you add, rename, or remove a locale key, make the equivalent change in every sibling locale file in the same `locales/` directory.
- Keep the locale key set identical across sibling locale files; do not leave a key present in only one language.
- Preserve the same placeholder names, interpolation variables, and pluralization structure across sibling locale files.
- If a translation is not ready, keep the key and add a temporary value instead of deleting or diverging the structure.
