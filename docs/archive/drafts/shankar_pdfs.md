This is the formidable repo. It works in 3 parts
1. the pwa web app (pwa/)
2. The form extraction pipeline which relies on aws textract run through the `good_shepherd` serverless server. This server is already deployed and you can find it using these credentials 

From within /home/desinotorious/src/github.com/bprashanth/good-shepherd
- Addresses: server/deploy/outputs.env
- Credentials: server/deploy/test-credentials.env


The same should be happening via the netlify.toml and the user login in the pwa.

3. The agent server, which processes and runs various per-column identification intelligence. You can find this in agent/.

As a first step i want you to document this. Keep it simple. But outline what calls what from the pwa. And outline the architecture which should be as follows: 
1. This is to detect ecological forms. As such, it will be processing columns post textract extraction with this idea. 
2. The ecological context is embedded in a set of handlers in the agent server. For example there is some fuzz matching on species names and local toda names, which uses a certain species dictionary. 
3. Every new type ecological column will typically happen through a handler here. Columns that are super obvious, like columns that just have numbers etc - don't really need a special handler. Textract will just remove these and put them into the excel and we can allow the user to figure it out. 
4. The Point is to perform a sort of "corrrection" - if textract guesses a certain column badly, we can apply the known ecological context from the user to "cheat" on that column. For example some columns are "tally" columns and this will be obvious from the fact that it's just lins in that column. These should be treated as a "type: tally" and the handler should count the number of ls or 1s put there by textract and replace it with a number. There is no need to implement this unless it's seen in the input forms - im just giving you an example. 

One you have processed and understood this, write the README. Don't duplicate info in the pwa/README.md and agent/README.md, link to those instead. And add a manual in docs/manuals/ for adding a new ecologicalcontext handling endpoint. 

Once we have done that we will move on to the real task. 
