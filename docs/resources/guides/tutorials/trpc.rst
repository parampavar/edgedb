.. _ref_guide_trpc:

====
tRPC
====

:edb-alt-title: Integrating Gel with tRPC

This guide explains how to integrate **Gel** with **tRPC** for a modern,
type-safe API. We'll cover setting up database interactions, API routing,
and implementing authentication, all while ensuring type safety across the
client and server.

You can reference the following repositories for more context:

- `create-t3-turbo-gel <https://github.com/geldata/create-t3-turbo-gel>`_ -
  A monorepo template using the `T3 stack <https://init.tips/>`_,
  `Turborepo <https://turbo.build/>`_, and Gel.
- `LookFeel Project <https://github.com/LewTrn/lookfeel>`_ - A real-world
  example using **Gel** and **tRPC**.

Step 1: Gel setup
=================

|Gel| will serve as the database layer for your application.

Install and initialize Gel
--------------------------

To initialize **Gel**, run the following command using your preferred
package manager:

.. code-block:: bash

   $ pnpm dlx gel project init # or `npx gel project init`

This will create a Gel project and set up a schema to start with.

Define the Gel Schema
---------------------

The previous command generated a schema file in the ``dbschema`` directory.

Here's an example schema that defines a ``User`` model:

.. code-block:: sdl
   :caption: dbschema/default.gel

   module default {
     type User {
       required name: str;
       required email: str;
     }
   }

Apply schema migrations
-----------------------

Once schema changes are made, apply migrations with:

.. code-block:: bash

   $ pnpm dlx gel migration create # or npx gel migration create
   $ pnpm dlx gel migration apply # or npx gel migration apply

Step 2: Configure Gel Client
============================

To interact with **Gel** from your application, you need to configure the
client.

Install Gel Client
------------------

First, install the **Gel** client using your package manager:

.. code-block:: bash

   $ pnpm add gel
   $ # or yarn add gel
   $ # or npm install gel
   $ # or bun add gel

Then, create a client instance in a ``gel.ts`` file:

.. code-block:: typescript
   :caption: src/gel.ts

   import { createClient } from 'gel';

   const gelClient = createClient();
   export default gelClient;

This client will be used to interact with the database and execute queries.

Step 3: tRPC setup
==================

**tRPC** enables type-safe communication between the frontend and
backend.

Install tRPC dependencies
-------------------------

Install the required tRPC dependencies:

.. code-block:: bash

   $ pnpm add @trpc/server @trpc/client
   $ # or yarn add @trpc/server @trpc/client
   $ # or npm install @trpc/server @trpc/client
   $ # or bun add @trpc/server @trpc/client

If you're using React and would like to use React Query with tRPC, also
install a wrapper around the `@tanstack/react-query <https://tanstack.com/query/latest>`_.

.. code-block:: bash

   $ pnpm add @trpc/react-query
   $ # or yarn add @trpc/react-query
   $ # or npm install @trpc/react-query
   $ # or bun add @trpc/react-query

Define the tRPC Router
-----------------------

Here's how to define a simple tRPC query that interacts with **Gel**:

.. code-block:: typescript
   :caption: server/routers/_app.ts

   import { initTRPC } from '@trpc/server';
   import gelClient from './gel';

   const t = initTRPC.create();

   export const appRouter = t.router({
     getUsers: t.procedure.query(async () => {
       const users = await gelClient.query('SELECT User { name, email }');
       return users;
     }),
   });

   export type AppRouter = typeof appRouter;

This example defines a query that fetches user data from Gel, ensuring
type safety in both the query and response.

Step 4: Use tRPC Client
========================

Now that the server is set up, you can use the tRPC client to interact with
the API from the frontend. We will demonstrate how to integrate tRPC with
**Next.js** and **Express**.

With Next.js
------------

If you're working with **Next.js**, here's how to integrate **tRPC**:

Create a tRPC API Handler
~~~~~~~~~~~~~~~~~~~~~~~~~

Inside ``api/trpc/[trpc].ts``, create the following handler to connect
**tRPC** with Next.js:

.. code-block:: typescript
   :caption: pages/api/trpc/[trpc].ts

   import { createNextApiHandler } from '@trpc/server/adapters/next';
   import { appRouter } from '../../../server/routers/_app';

   export default createNextApiHandler({
     router: appRouter,
   });

Create a tRPC Client
~~~~~~~~~~~~~~~~~~~~

Next, create a **tRPC** client to interact with the API:

.. code-block:: typescript
   :caption: utils/trpc.ts

   import { createTRPCReact } from "@trpc/react-query";
   import { AppRouter } from './routers/_app';

   export const api = createTRPCReact<AppRouter>();

Client-Side Usage in Next.js
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You can then use **tRPC** hooks to query the API from the client:

.. code-block:: typescript
   :caption: components/UsersComponent.tsx

   import { trpc } from '../utils/trpc';

   const UsersComponent = () => {
     const { data, isLoading } = trpc.getUsers.useQuery();

     if (isLoading) return <div>Loading...</div>;

     return (
       <div>
         {data?.map(user => (
           <p key={user.email}>{user.name}</p>
         ))}
       </div>
     );
   };

   export default UsersComponent;

Alternative Path: Use tRPC with Express
---------------------------------------

If you're not using **Next.js**, here's how you can integrate **tRPC** with
**Express**.

Set up Express server with tRPC
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Here's how you can create an Express server and integrate **tRPC**:

.. code-block:: typescript

   import express from 'express';
   import { appRouter } from './routers/_app';
   import * as trpcExpress from '@trpc/server/adapters/express';

   const app = express();

   app.use(
     '/trpc',
     trpcExpress.createExpressMiddleware({
       router: appRouter,
     })
   );

   app.listen(4000, () => {
     console.log('Server is running on port 4000');
   });

Client-side usage
-----------------

In non-Next.js apps, use the tRPC client to interact with the server:

.. code-block:: typescript

   import { createTRPCClient, httpBatchLink } from '@trpc/client';
   import { AppRouter } from './routers/_app';

   const trpc = createTRPCClient<AppRouter>({
     links: [
       httpBatchLink({
         url: 'http://localhost:4000/trpc',
       }),
     ],
   });

   async function fetchUsers() {
     const users = await trpc.getUsers.query();
     console.log(users);
   }

Step 5: Set up authentication with Gel Auth
===========================================

In this section, we will cover how to integrate **Gel Auth** with **tRPC**
and context in both **Next.js** and **Express** environments. This will ensure
that user authentication is handled securely and that both server-side and
client-side tRPC calls can access the user's session.

Gel Auth with tRPC and tRPC context in Next.js
----------------------------------------------

In **Next.js**, integrating **Gel Auth** with **tRPC** involves creating a
context that provides the user session and Gel client to the tRPC API.

1. **Initialize Gel Client and Auth**

   First, initialize the **Gel** client and **Gel Auth**:

   .. code-block:: typescript

      import { createClient } from "gel";
      import createAuth from "@gel/auth-nextjs/app";

      // Initialize Gel client
      export const gelClient = createClient();

      // Initialize Gel Auth
      export const auth = createAuth(gelClient, {
        baseUrl: process.env.VERCEL_ENV === "production"
          ? "https://production.yourapp.com"
          : "http://localhost:3000",
      });

2. **Create tRPC Context**

   The **tRPC** context provides the Gel Auth session to the tRPC
   procedures:

   .. code-block:: typescript
      :caption: src/trpc.ts

      import { initTRPC } from '@trpc/server';
      import { headers } from "next/headers";
      import { auth } from "src/gel.ts";

      // Create tRPC context with session and Gel client
      export const createTRPCContext = async () => {
        const session = await auth.getSession(); // Retrieve session from Gel Auth

        return {
          session, // Pass the session to the context
        };
      };

      // Initialize tRPC with context
      const t = initTRPC.context<typeof createTRPCContext>().create({});

3. **Use tRPC Context in API Handler**

   In **Next.js**, set up an API handler to connect your **tRPC router** with
   the context:

   .. code-block:: typescript
      :caption: pages/api/trpc/[trpc].ts

      import { createNextApiHandler } from '@trpc/server/adapters/next';
      import { createTRPCContext } from 'src/trpc.ts';
      import { appRouter } from 'src/routers/_app';

      export default createNextApiHandler({
        router: appRouter, // Your tRPC router
        createContext: createTRPCContext,
      });

4. **Example tRPC Procedure**

   You can now write procedures in your tRPC router, making use of the
   **Gel Auth** session and the **Gel** client:

   .. code-block:: typescript

      export const appRouter = t.router({
        getUserData: t.procedure.query(async ({ ctx }) => {
          if (!(await ctx.session.isSignedIn())) {
            throw new Error("Not authenticated");
          }
          // Fetch data from Gel using the authenticated client
          const userData = await ctx.session.client.query(`
            select User { name, email }
          `);

          return userData;
        }),
      });

Gel Auth with tRPC and Context in Express
-----------------------------------------

In **Express**, the process involves setting up middleware to manage the
authentication and context for tRPC procedures.

1. **Initialize Gel Client and Auth for Express**

   Just like in **Next.js**, you first initialize the **Gel** client and
   **Gel Auth**:

   .. code-block:: typescript

      import { createClient } from "gel";
      import createExpressAuth from "@gel/auth-express";

      // Initialize Gel client
      const gelClient = createClient();

      // Initialize Gel Auth for Express
      export const auth = createExpressAuth(gelClient, {
        baseUrl: `http://localhost:${process.env.PORT || 3000}`,
      });

2. **Create tRPC Context Middleware for Express**

   In **Express**, create middleware to pass the authenticated session and
   Gel client to the tRPC context:

   .. code-block:: typescript

      import { type AuthRequest, type Response, type NextFunction } from "express";

      // Middleware to set up tRPC context in Express
      export const createTRPCContextMiddleware = async (
        req: AuthRequest,
        res: Response,
        next: NextFunction
      ) => {
        const session = req.auth?.session(); // Get authenticated session
        req.context = {
          session, // Add session to context
          gelClient, // Add Gel client to context
        };
        next();
      };

3. **Set up tRPC Router in Express**

   Use the **tRPC router** in **Express** by including the context middleware
   and **Gel Auth** middleware:

   .. code-block:: typescript

      import express from "express";
      import { appRouter } from "./path-to-router";
      import { auth } from "./path-to-auth";
      import { createTRPCContextMiddleware } from "./path-to-context";
      import { createExpressMiddleware } from "@trpc/server/adapters/express";

      const app = express();

      // Gel Auth middleware to handle sessions
      app.use(auth.middleware);

      // Custom middleware to pass tRPC context
      app.use(createTRPCContextMiddleware);

      // tRPC route setup
      app.use(
        "/trpc",
        createExpressMiddleware({
          router: appRouter,
          createContext: (req) => req.context, // Use context from middleware
        })
      );

      app.listen(4000, () => {
        console.log('Server running on port 4000');
      });

4. **Example tRPC Procedure in Express**

   Once the context is set, you can define tRPC procedures that use both the
   session and Gel client:

   .. code-block:: typescript

      export const appRouter = t.router({
        getUserData: t.procedure.query(async ({ ctx }) => {
          if (!(await ctx.session.isSignedIn())) {
            throw new Error("Not authenticated");
          }
          // Fetch data from Gel using the authenticated client
          const userData = await ctx.session.client.query(`
            select User { name, email }
          `);

          return userData;
        }),
      });

Conclusion
----------

By integrating **Gel Auth** into the tRPC context, you ensure that
authenticated sessions are securely passed to API procedures, enabling
user authentication and protecting routes.

You can also reference these projects for further examples:

- `create-t3-turbo-gel <https://github.com/geldata/create-t3-turbo-gel>`_ -
  A monorepo template using the `T3 stack <https://init.tips/>`_,
  `Turborepo <https://turbo.build/>`_, and Gel.
- `LookFeel Project <https://github.com/LewTrn/lookfeel>`_ - A real-world
  example using **Gel** and **tRPC**.
