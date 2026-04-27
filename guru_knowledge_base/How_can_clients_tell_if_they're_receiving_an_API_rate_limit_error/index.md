# How can clients tell if they're receiving an API rate limit error?

> **Collection:** Customer Success
> **Last Modified:** 2023-11-16
> **Tags:** api, API call, API token, Delia, integration

---

The technical details about rate limit-related data we provide on the responses:

For requests failing due to rate limit, you get this response:

HTTP Code: 429 (Too Many Requests)

Response Body:

**{**

**    "message": "Too Many Attempts.",**

**    "code": 0**

**}**

Relevant Headers:

- X-RateLimit-Limit - the limit of requests/min
- Retry-After - (in seconds) wait time until the limit resets
- X-RateLimit-Reset - exact timestamp when the limit resets



We also respond with rate limit-related headers on successful requests:

- X-RateLimit-Limit - the max. number of requests/min
- X-RateLimit-Remaining: - remaining number requests in the interval



These Technical details can be sent to the person or tool handling the scripts to fix and adjust the limit.
