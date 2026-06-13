<script setup lang="ts">
import { formatMoneyMinor } from "../lib/money";

defineProps<{
  report: {
    hard_failures: Array<{
      label: string;
      entity_name: string;
      month?: string | null;
      absolute_delta_minor?: number | null;
    }>;
    warnings: Array<{ message: string }>;
    checks: Array<{
      label: string;
      entity_name: string;
      month?: string | null;
      passed: boolean;
      absolute_delta_minor?: number | null;
    }>;
  } | null;
}>();
</script>

<template>
  <div v-if="report" class="validation-report">
    <h3>Validation report</h3>
    <div>
      <strong>Hard failures</strong>
      <ul>
        <li
          v-for="failure in report.hard_failures"
          :key="`${failure.label}-${failure.entity_name}-${failure.month ?? 'all'}`"
        >
          {{ failure.label }} · {{ failure.entity_name
          }}<span v-if="failure.month"> · {{ failure.month }}</span
          ><span
            v-if="
              failure.absolute_delta_minor !== undefined &&
              failure.absolute_delta_minor !== null
            "
          >
            · delta {{ formatMoneyMinor(failure.absolute_delta_minor) }}</span
          >
        </li>
      </ul>
    </div>
    <div>
      <strong>Warnings</strong>
      <ul>
        <li v-for="warning in report.warnings" :key="warning.message">
          {{ warning.message }}
        </li>
      </ul>
    </div>
    <div>
      <strong>Checks</strong>
      <ul>
        <li
          v-for="check in report.checks"
          :key="`${check.label}-${check.entity_name}-${check.month ?? 'all'}`"
        >
          {{ check.label }} · {{ check.entity_name
          }}<span v-if="check.month"> · {{ check.month }}</span> ·
          {{ check.passed ? "pass" : "fail"
          }}<span
            v-if="
              check.absolute_delta_minor !== undefined &&
              check.absolute_delta_minor !== null
            "
          >
            · delta {{ formatMoneyMinor(check.absolute_delta_minor) }}</span
          >
        </li>
      </ul>
    </div>
  </div>
</template>
