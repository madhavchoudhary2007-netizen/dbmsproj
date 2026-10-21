import { defineConfig, globalIgnores } from "eslint/config";
import nextVitals from "eslint-config-next/core-web-vitals";
import tseslint from "typescript-eslint";

export default defineConfig([
  ...nextVitals,
  {
    plugins: { "@typescript-eslint": tseslint.plugin },
    rules: {
      "react-hooks/set-state-in-effect": "off",
      "react/no-children-prop": "off",
      "@typescript-eslint/no-explicit-any": "error",
    },
  },
  globalIgnores([".next/**", "out/**", "build/**", "next-env.d.ts"]),
]);
