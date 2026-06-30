// <Name>.fixtures.ts
//
// Colocated fixture contract for a shared component.
// Both the /dev/design-system catalog page and Cypress component tests import
// this same object. Keep scenarios representative, deterministic, and visually
// useful; exhaustive behavior coverage belongs in tests.

import ExampleComponent from './ExampleComponent.vue'
import type { ComponentFixtureSet } from '../fixtures'

type ExampleProps = InstanceType<typeof ExampleComponent>['$props']

const fixtures: ComponentFixtureSet<ExampleProps> = {
  component: ExampleComponent,
  title: 'Example Component',
  description: 'Representative scenarios for design-system review.',
  presentation: {
    viewport: 'medium',
    container: 'padded',
  },
  scenarios: [
    {
      name: 'default',
      description: 'Normal resting state.',
      props: {
        label: 'Groceries',
        amount: 132.0,
      },
    },
    {
      name: 'overflow',
      description: 'Long text and larger content pressure.',
      props: {
        label: 'Renter insurance and utilities sinking fund transfer',
        amount: 920.5,
      },
      presentation: {
        viewport: 'narrow',
      },
      notes: 'Use fixed literal values only; never compute dates or amounts at runtime.',
    },
  ],
}

export default fixtures
