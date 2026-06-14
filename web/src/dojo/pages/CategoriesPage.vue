<script setup lang="ts">
import CategoryEditor from "../components/CategoryEditor.vue";
import CategoryGroupEditor from "../components/CategoryGroupEditor.vue";
import CategoryReorderControl from "../components/CategoryReorderControl.vue";
import CategoryVisibilityToggle from "../components/CategoryVisibilityToggle.vue";
import PageHeader from "../components/PageHeader.vue";
import Panel from "../components/Panel.vue";
import { useAppState } from "../state/app";
import type { Category } from "../types";

const app = useAppState();

function toggleVisibility(category: Category, hidden: boolean): void {
  app.saveCategory({ is_hidden: hidden }, category.category_id);
}

function updateSortOrder(category: Category, sortOrder: number): void {
  app.saveCategory({ sort_order: sortOrder }, category.category_id);
}
</script>

<template>
  <div class="page-grid">
    <PageHeader
      title="Categories"
      subtitle="Manage groups, categories, order, and hidden state."
    />
    <div class="editor-grid">
      <Panel>
        <CategoryGroupEditor @submit="app.saveCategoryGroup($event)" />
      </Panel>
      <Panel>
        <CategoryEditor
          :groups="app.state.categoryGroups"
          @submit="app.saveCategory($event)"
        />
      </Panel>
    </div>
    <Panel>
      <table class="category-table">
        <thead>
          <tr>
            <th>Group</th>
            <th>Category</th>
            <th>Order</th>
            <th>Visibility</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="category in app.state.categories"
            :key="category.category_id"
          >
            <td>{{ category.group_name }}</td>
            <td>{{ category.name }}</td>
            <td>
              <CategoryReorderControl
                :sort-order="category.sort_order"
                @update="updateSortOrder(category, $event)"
              />
            </td>
            <td>
              <CategoryVisibilityToggle
                :hidden="category.is_hidden"
                @toggle="toggleVisibility(category, $event)"
              />
            </td>
          </tr>
        </tbody>
      </table>
    </Panel>
  </div>
</template>

<style scoped>
.page-grid,
.editor-grid {
  display: grid;
  gap: 1rem;
}

.editor-grid {
  grid-template-columns: repeat(auto-fit, minmax(18rem, 1fr));
}

.category-table {
  width: 100%;
  border-collapse: collapse;
}

th,
td {
  border: 1px solid var(--dojo-border-tan);
  padding: 0.5rem;
  text-align: left;
}
</style>
