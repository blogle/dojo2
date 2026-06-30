# Cypress component testing -- setup and fixture-driven workflow

Loaded from the `cypress-testing` skill when writing or debugging component
tests. See `visual-regression.md` for snapshot-specific guidance.

## Firm choices

- Use `cypress/vue` mounting with the Vite dev server.
- Use stable `data-cy` selectors for interactive elements.
- Mount scenarios from the colocated fixture object rather than repeating props
  inline.

## Setup

```ts
// cypress.config.ts
import { defineConfig } from 'cypress'

export default defineConfig({
  component: {
    devServer: { framework: 'vue', bundler: 'vite' },
    specPattern: 'web/src/dojo/components/**/*.cy.ts',
    viewportWidth: 1280,
    viewportHeight: 800,
  },
})
```

```ts
// cypress/support/component.ts
import { mount } from 'cypress/vue'

Cypress.Commands.add('mount', (component, options = {}) => {
  options.global = options.global ?? {}
  options.global.stubs = options.global.stubs ?? {}
  options.global.stubs.transition = false
  return mount(component, options)
})
```

## Generate tests from fixtures

```ts
import fixtures from './Button.fixtures'

describe('Button', () => {
  fixtures.scenarios.forEach((scenario) => {
    it(`renders: ${scenario.name}`, () => {
      cy.mount(fixtures.component, {
        props: scenario.props,
        slots: scenario.slots,
      })
      cy.get('[data-cy=button-root]').should('be.visible')
    })
  })
})
```

If a particular scenario needs a behavior assertion beyond "it rendered," add
targeted tests for that scenario. Do not bloat the fixture file into an
exhaustive behavior matrix.

## Gotchas

- Share the same Pinia instance between the mounted component and any store
  assertions.
- Teleport content is queryable in Cypress without special wrapper hacks.
- Stub network requests with fixed fixtures.
- Do not use fixed `cy.wait(...)` sleeps.
