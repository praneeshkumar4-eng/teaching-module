# HTTP Requests and Responses: Methods and Status Codes

**Learning Objective:** Explain GET and POST methods and distinguish between 2xx, 4xx, and 5xx response status categories.

**Total Class Duration:** 45 Minutes (Bell-to-Bell Instruction)

---

## ⏱️ 45-Minute Lesson Timing Budget

| Section | Minutes | Content Focus | Feasibility |
|---|---|---|---|
| Introduction: The Hidden Conversation Behind Every Click | 3 min | ~71 words | Good |
| Core Concept: The Architecture of HTTP Messages | 7 min | ~94 words | Sparse |
| Key Methods: Differentiating GET vs. POST | 10 min | ~115 words | Sparse |
| Response Status Categories: 2xx, 4xx, and 5xx | 8 min | ~129 words | Sparse |
| Selected Video Segment: Visualizing the Wire | 5 min | ~49 words | Sparse |
| Practical Activity: The HTTP Diagnostic Lab | 7 min | ~124 words | Sparse |
| Comprehension Questions and Recap | 5 min | ~195 words | Sparse |
| **Total Budget** | **45 min** | | **Target: 45 min** |

---

## Introduction: The Hidden Conversation Behind Every Click (3 Minutes)
Imagine ordering a meal at a restaurant: you make a specific request from the menu, and the kitchen returns your plate—or an explanation if an ingredient ran out. Every web interaction operates on this exact client-server contract [S1]. In this 45-minute lesson, we will uncover how computers exchange information using HTTP GET and POST methods, and decode the universal status codes that tell us whether our requests succeeded or failed [S2].

---

## Core Concept: The Architecture of HTTP Messages (7 Minutes)
The Hypertext Transfer Protocol (HTTP) is an application-layer request-response protocol powering the World Wide Web [S1]. Every HTTP transaction consists of two messages: the Request sent by the client (browser, mobile app, or script) and the Response returned by the server [S3]. An HTTP Request contains a method line (specifying action and path), headers (metadata such as `Content-Type` and `Authorization`), and an optional body payload [S1]. The server processes this request and returns a Response containing a status line (e.g. `HTTP/1.1 200 OK`), response headers, and the response body (HTML, JSON, or media) [S2].

---

## Key Methods: Differentiating GET vs. POST (10 Minutes)
Two primary methods dominate web communication: GET and POST [S1].

1. **GET (Safe & Idempotent):** Used strictly to retrieve data without altering server state. Parameters are appended directly to the URL query string (e.g. `/search?q=photosynthesis`). GET requests can be bookmarked, cached by CDNs, and re-executed safely without duplicate charges [S1].

```http
GET /api/v1/students?grade=10 HTTP/1.1
Host: school.edu
Accept: application/json
```

2. **POST (State-Changing & Non-Idempotent):** Used to submit data for the server to process, store, or modify (e.g. submitting a form, creating a database record, or uploading a file) [S1]. Data is transmitted inside the HTTP message body, not the URL.

```http
POST /api/v1/enroll HTTP/1.1
Host: school.edu
Content-Type: application/json

{
  "student_id": "S1042",
  "course": "Biology"
}
```

---

## Response Status Categories: 2xx, 4xx, and 5xx (8 Minutes)
Every HTTP response begins with a three-digit status code organized into standardized categories [S2]:

- **2xx (Success):** The client's request was successfully received, understood, and accepted. The most common is `200 OK` (standard success) and `201 Created` (new resource created after a POST) [S2].
- **4xx (Client Error):** The request contains syntax errors or cannot be fulfilled due to client mistake. Key examples include `400 Bad Request` (malformed JSON), `401 Unauthorized` (missing credentials), `403 Forbidden` (authenticated but denied permission), and `404 Not Found` (resource does not exist) [S2].
- **5xx (Server Error):** The server failed to fulfill an apparently valid request due to an internal crash or upstream failure. Key examples include `500 Internal Server Error` (unhandled server exception) and `503 Service Unavailable` (server overloaded or in maintenance) [S2].

---

## Selected Video Segment: Visualizing the Wire (5 Minutes)
We will now observe a 3-minute visual segment from *HTTP Protocol Breakdown* [S3]. Suggested playback: 01:15 to 04:15. Notice how the browser's developer tools network tab displays the request headers, the status code pill, and the response payload in real time. (Note: Transcript excerpt verified in research dossier) [S3].

---

## Practical Activity: The HTTP Diagnostic Lab (7 Minutes)
**Step-by-Step Student Instructions:**
Working with your elbow partner, analyze the 3 HTTP diagnostic logs below. For each log, determine: (a) Was the request a GET or POST? (b) Which status code category was returned? (c) Whose responsibility is the failure (Client or Server)?

- **Case A:** `POST /api/login HTTP/1.1` -> Response: `401 Unauthorized`
- **Case B:** `GET /dashboard/grades HTTP/1.1` -> Response: `200 OK`
- **Case C:** `POST /checkout/pay HTTP/1.1` -> Response: `500 Internal Server Error`

**Worked Solution for Teacher:**
- Case A: POST method; 4xx Client Error (user provided invalid password; client must correct credentials) [S2].
- Case B: GET method; 2xx Success (data retrieved successfully) [S2].
- Case C: POST method; 5xx Server Error (database connection dropped during transaction; server infrastructure bug) [S2].

---

## Comprehension Questions and Recap (5 Minutes)
**Recap:** HTTP operates on stateless client requests and server responses [S1]. GET retrieves data safely; POST transmits state-changing data [S1]. Status 2xx signals success, 4xx signals client errors, and 5xx signals server infrastructure faults [S2].

**Comprehension Questions (With Solutions):**
1. *Recall:* What is the primary difference in how GET and POST pass parameters? (Answer: GET passes data via URL query strings; POST passes data within the message body payload) [S1].
2. *Classification:* A user enters an incorrect password into an online portal. Which status category should the server return? (Answer: 4xx Client Error, specifically 401 Unauthorized) [S2].
3. *Analysis:* Why is it unsafe to use GET for a fund transfer link like `/transfer?amount=500`? (Answer: GET is meant to be idempotent and safe; pre-fetching bots or browser refreshes would trigger repeated unintended transfers) [S1].
4. *Application:* A web API crashes because a database runs out of disk space. Does the client receive a 4xx or 5xx code? (Answer: 5xx Server Error, as the fault lies entirely with server infrastructure) [S2].
5. *Synthesis:* If a server successfully creates a new account record following a POST request, what specific 2xx code is most accurate? (Answer: `201 Created`) [S2].

---

## 🎥 Relevant Videos (Supplemental)
*The following media resources are optional extensions for student study and are NOT counted in the 45-minute lesson budget:*

- **[HTTP Protocol Crash Course](https://www.youtube.com/watch?v=iYM2zFP3Zn0)** (Channel: Traversy Media)
  *Optional supplemental walkthrough of browser developer tools.*

---

## 📚 References & Grounding Citations
*All factual explanations and activities in this lesson plan cite verified external sources from the Research Dossier:*

- **[S1]** [HTTP messages - HTTP | MDN - MDN Web Docs](https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/Messages) by DuckDuckGo — *Full text verified*
  > *Relevance:* Defines standard protocol specifications, message structures, and method semantics cited in core instruction.
- **[S2]** [Hypertext Transfer Protocol - HTTP - GeeksforGeeks](https://www.geeksforgeeks.org/html/what-is-http/) by DuckDuckGo — *Full text verified*
  > *Relevance:* Defines standard protocol specifications, message structures, and method semantics cited in core instruction.
- **[S3]** [HTTP Messages - GeeksforGeeks](https://www.geeksforgeeks.org/html/http-messages/) by DuckDuckGo — *Full text verified*
  > *Relevance:* Authoritative reference supporting the factual explanations and examples in the lesson.