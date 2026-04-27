# Allowed characters for keywords and group names

> **Collection:** Customer Success
> **Last Modified:** 2025-02-19
> **Tags:** allowed characters, Mircea, special characters

---

We generally accept all special language characters.

The allowed characters are:

- For Groups/Folders: 

```
`a-z A-Z 0-9 - _ . $ % @ # & ' : () a-zA-Z\p{L}\p{Mn}\p{Thai} (no / or \ allowed) - no slash / or backword slash \ allowed`
```

- For Keywords: 

```
`a-z A-Z 0-9 + - . ' $ % @ # () & _ a-zA-Z\p{L}\p{Mn}\p{Thai}/`
```



Extra: Our REGEX works with a 'u' modifier (PCRE_UTF8), validating the input as **UTF-8**, starting with the detection of unallowed characters.

- RegEx  - Folders: `/[^:()a-zA-Z0-9-_. $%@#&'a-zA-Z\p{L}\p{Mn}\p{Thai}]/u`
- RegEx  - Keywords: `/[^+a-zA-Z0-9-. '$%@#()&_a-zA-Z\p{L}\p{Mn}\p{Thai}\/]/u`

​Special mentions 

- the most recent addition is `p{Mn}` - “\p{Mn} or \p{Non_Spacing_Mark}: a character intended to be combined with another character without taking up extra space (e.g. accents, umlauts, etc.).”
- the special foreign characters, such as Arabic, fall under the \p{L}  code
