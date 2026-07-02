# Eval Fixture: Coincidental Vue Similarity

The patch proposes extracting these two components into one generic `ListPanel` because both render a heading and a list.

```vue
<!-- RecentTransactions.vue -->
<section>
  <h2>Recent transactions</h2>
  <ul>
    <li v-for="transaction in transactions" :key="transaction.id">
      {{ transaction.payee }} · {{ formatCurrency(transaction.amountMinor) }}
    </li>
  </ul>
</section>
```

```vue
<!-- ImportWarnings.vue -->
<section>
  <h2>Import warnings</h2>
  <ul>
    <li v-for="warning in warnings" :key="warning.code">
      {{ warning.message }}
    </li>
  </ul>
</section>
```

The proposed `ListPanel` would accept `title`, `items`, `itemKey`, and `renderItem` props.
