<script setup lang="ts">
defineProps<{
  report: {
    hard_failures: Array<{ label: string }>;
    warnings: Array<{ message: string }>;
    checks: Array<{ label: string; passed: boolean }>;
  } | null;
}>();
</script>

<template>
  <div v-if="report" class="validation-report">
    <h3>Validation report</h3>
    <div>
      <strong>Hard failures</strong>
      <ul>
        <li v-for="failure in report.hard_failures" :key="failure.label">{{ failure.label }}</li>
      </ul>
    </div>
    <div>
      <strong>Warnings</strong>
      <ul>
        <li v-for="warning in report.warnings" :key="warning.message">{{ warning.message }}</li>
      </ul>
    </div>
    <div>
      <strong>Checks</strong>
      <ul>
        <li v-for="check in report.checks" :key="check.label">{{ check.label }} · {{ check.passed ? "pass" : "fail" }}</li>
      </ul>
    </div>
  </div>
</template>
