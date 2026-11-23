## Frontend dependencies

The frontend uses:

- **React and React DOM** to build and render the interface.
- **Vite and `@vitejs/plugin-react`** to run and build the React app.
- **MUI Material and MUI Icons** for interface components and icons.
- **MUI X Data Grid** for the orders table.
- **Emotion** as MUI’s styling engine.
- **React Router** for navigation between pages.
- **Concurrently** to start the frontend and backend together.
- **ESLint** to check frontend code for common issues.

Install the frontend dependencies from the repository root:

```bash
npm --prefix frontend install
```

## Run the dashboard

Make sure the project’s `.venv` exists at the repository root and the backend’s Python dependencies are installed in it. Node.js and npm must also be installed.

From the repository root, start the backend and frontend with:

```bash
npm --prefix frontend run dev
```

Open the Vite address shown in the terminal, usually `http://localhost:5173`. Press `Ctrl+C` to stop both servers.