<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from "vue";

import type {
  ComponentFixtureScenario,
  ComponentFixtureSet,
  FixturePresentation,
} from "@/dojo/components/fixtures";
import Divider from "@/dojo/components/layout/Divider.vue";
import NavigationRail from "@/dojo/components/navigation/NavigationRail.vue";
import FixtureScenarioRenderer from "@/dojo/design-system/FixtureScenarioRenderer";
import { fixtureRegistry } from "@/dojo/design-system/fixtureRegistry";
import manifest from "@/dojo/design-system/manifest";

interface CatalogEntry {
  component: string;
  fixturePath: string;
  fixture: ComponentFixtureSet;
}

interface CatalogSection {
  id: string;
  title: string;
  description?: string;
  entries: CatalogEntry[];
}

const introFixture = fixtureRegistry[manifest.page_shell.intro.fixture];
const railExpanded = ref(false);
const isCompactRail = ref(false);

const compactRailMediaQuery = "(max-width: 720px)";
let compactRailMatcher: MediaQueryList | null = null;

const syncCompactRail = (matches: boolean) => {
  isCompactRail.value = matches;

  if (matches) {
    railExpanded.value = false;
  }
};

const handleCompactRailChange = (event: MediaQueryListEvent) => {
  syncCompactRail(event.matches);
};

onMounted(() => {
  compactRailMatcher = window.matchMedia(compactRailMediaQuery);
  syncCompactRail(compactRailMatcher.matches);
  compactRailMatcher.addEventListener("change", handleCompactRailChange);
});

onBeforeUnmount(() => {
  compactRailMatcher?.removeEventListener("change", handleCompactRailChange);
});

const railIsExpanded = computed(
  () => railExpanded.value && !isCompactRail.value,
);
const railWidth = computed(() =>
  railIsExpanded.value
    ? "var(--space-nav-expanded)"
    : "var(--space-nav-collapsed)",
);

const sections = computed<CatalogSection[]>(() =>
  manifest.sections.map((section) => ({
    ...section,
    entries: section.entries.map((entry) => ({
      component: entry.component,
      fixturePath: entry.fixture,
      fixture: fixtureRegistry[entry.fixture],
    })),
  })),
);

const quickNavItems = computed(() =>
  sections.value.map((section, index) => ({
    kind: "anchor" as const,
    key: section.id,
    label: `${index + 1}. ${section.title}`,
    visibleLabel: section.title,
    icon: index === 0 ? "foundations" : index === 1 ? "layout" : "navigation",
    href: `#${section.id}`,
  })),
);

const sectionHeading = (index: number, title: string) =>
  manifest.page_shell.section_heading_format
    .replace("{index}", String(index + 1))
    .replace("{title}", title);

const scenarioPresentation = (
  fixture: ComponentFixtureSet,
  scenario: ComponentFixtureScenario,
): FixturePresentation => ({
  ...fixture.presentation,
  ...scenario.presentation,
});

const scenarioClasses = (presentation: FixturePresentation) => [
  "design-system-page__scenario-canvas",
  presentation.viewport
    ? `design-system-page__scenario-canvas--${presentation.viewport}`
    : "",
  presentation.container
    ? `design-system-page__scenario-canvas--${presentation.container}`
    : "",
];

const showScenarioName = (
  fixture: ComponentFixtureSet,
  scenario: ComponentFixtureScenario,
) => !(fixture.scenarios.length === 1 && scenario.name === "default");
</script>

<template>
  <main
    class="design-system-page"
    data-cy="design-system-page-root"
    :style="{ '--rail-width': railWidth }"
  >
    <aside
      class="design-system-page__nav-shell"
      data-cy="design-system-page-nav-shell"
    >
      <NavigationRail
        :items="quickNavItems"
        :expanded="railIsExpanded"
        :collapsible="!isCompactRail"
        :full-height="true"
        aria-label="Design system sections"
        @toggle="railExpanded = !railExpanded"
      />
    </aside>

    <div
      class="design-system-page__container"
      data-cy="design-system-page-container"
      :style="{
        maxWidth: manifest.page_shell.container_max_width,
        '--section-gap': manifest.page_shell.section_gap,
        '--section-heading-gap':
          manifest.page_shell.section_heading_gap ?? 'var(--space-xl)',
      }"
    >
      <header class="design-system-page__header">
        <p class="design-system-page__eyebrow">dojo</p>
        <h1 class="design-system-page__title">Dojo Design System</h1>
        <p class="design-system-page__summary">
          Tokens, layout primitives, and shared component specimens.
        </p>
      </header>

      <section class="design-system-page__intro">
        <FixtureScenarioRenderer
          :fixture="introFixture"
          :scenario="introFixture.scenarios[0]"
        />
      </section>

      <section
        v-for="(section, sectionIndex) in sections"
        :id="section.id"
        :key="section.id"
        class="design-system-page__section"
      >
        <header class="design-system-page__section-header">
          <h2 class="design-system-page__section-title">
            {{ sectionHeading(sectionIndex, section.title) }}
          </h2>
          <Divider />
          <p
            v-if="section.description"
            class="design-system-page__section-description"
          >
            {{ section.description }}
          </p>
        </header>

        <div class="design-system-page__entries">
          <article
            v-for="entry in section.entries"
            :key="entry.fixturePath"
            class="design-system-page__entry"
          >
            <div class="design-system-page__entry-copy">
              <h3 class="design-system-page__entry-title">
                {{ entry.fixture.title }}
              </h3>
              <p
                v-if="entry.fixture.description"
                class="design-system-page__entry-description"
              >
                {{ entry.fixture.description }}
              </p>
            </div>

            <div class="design-system-page__scenarios">
              <section
                v-for="scenario in entry.fixture.scenarios"
                :key="`${entry.component}-${scenario.name}`"
                class="design-system-page__scenario"
              >
                <div class="design-system-page__scenario-header">
                  <p
                    v-if="showScenarioName(entry.fixture, scenario)"
                    class="design-system-page__scenario-name"
                  >
                    {{ scenario.name }}
                  </p>
                  <p
                    v-if="scenario.description"
                    class="design-system-page__scenario-description"
                  >
                    {{ scenario.description }}
                  </p>
                </div>

                <div
                  :class="
                    scenarioClasses(
                      scenarioPresentation(entry.fixture, scenario),
                    )
                  "
                >
                  <FixtureScenarioRenderer
                    :fixture="entry.fixture"
                    :scenario="scenario"
                  />
                </div>

                <p
                  v-if="scenario.notes"
                  class="design-system-page__scenario-notes"
                >
                  {{ scenario.notes }}
                </p>
              </section>
            </div>
          </article>
        </div>
      </section>
    </div>
  </main>
</template>

<style scoped>
.design-system-page {
  min-height: 100vh;
  padding: var(--space-page-block) var(--space-page-inline) var(--space-3xl);
  display: flex;
  justify-content: flex-start;
  background: var(--color-background);
}

.design-system-page__nav-shell {
  position: fixed;
  top: 0;
  bottom: 0;
  left: 0;
  width: var(--rail-width);
  display: flex;
  z-index: 1;
}

.design-system-page__container {
  width: min(100%, var(--layout-page-max-width));
  display: grid;
  gap: var(--section-gap);
  margin-left: calc(var(--rail-width) + var(--space-page-inline));
  transition: margin-left var(--motion-normal) var(--motion-ease-out);
}

.design-system-page__header {
  display: grid;
  gap: var(--space-xs);
}

.design-system-page__eyebrow,
.design-system-page__summary,
.design-system-page__section-description,
.design-system-page__entry-description,
.design-system-page__scenario-description,
.design-system-page__scenario-notes {
  color: var(--color-on-surface-muted);
}

.design-system-page__eyebrow,
.design-system-page__scenario-name {
  margin: 0;
  font-family: var(--text-label-sm-font-family);
  font-size: var(--text-label-sm-font-size);
  font-weight: var(--text-label-sm-font-weight);
  line-height: var(--text-label-sm-line-height);
  letter-spacing: var(--text-label-sm-letter-spacing, 0.01em);
  text-transform: uppercase;
}

.design-system-page__title,
.design-system-page__summary,
.design-system-page__section-title,
.design-system-page__section-description,
.design-system-page__entry-title,
.design-system-page__entry-description,
.design-system-page__scenario-description,
.design-system-page__scenario-notes,
.design-system-page__scenario-name {
  margin: 0;
}

.design-system-page__title {
  color: var(--color-on-surface);
  font-family: var(--text-headline-lg-font-family);
  font-size: var(--text-headline-lg-font-size);
  font-weight: var(--text-headline-lg-font-weight);
  line-height: var(--text-headline-lg-line-height);
  letter-spacing: var(--text-headline-lg-letter-spacing);
}

.design-system-page__summary,
.design-system-page__section-description,
.design-system-page__entry-description,
.design-system-page__scenario-description,
.design-system-page__scenario-notes {
  font-family: var(--text-body-md-font-family);
  font-size: var(--text-body-md-font-size);
  font-weight: var(--text-body-md-font-weight);
  line-height: var(--text-body-md-line-height);
}

.design-system-page__intro,
.design-system-page__entries,
.design-system-page__scenarios {
  display: grid;
  gap: var(--layout-entry-gap);
}

.design-system-page__section {
  display: grid;
  gap: var(--section-heading-gap);
}

.design-system-page__section-header {
  display: grid;
  gap: var(--space-sm);
}

.design-system-page__section-title,
.design-system-page__entry-title {
  color: var(--color-on-surface);
}

.design-system-page__section-title {
  font-family: var(--text-headline-sm-font-family);
  font-size: var(--text-headline-sm-font-size);
  font-weight: var(--text-headline-sm-font-weight);
  line-height: var(--text-headline-sm-line-height);
}

.design-system-page__entry {
  display: grid;
  gap: var(--space-md);
}

.design-system-page__entry-copy {
  display: grid;
  gap: var(--space-xs);
}

.design-system-page__entry-title {
  font-family: var(--text-label-lg-font-family);
  font-size: var(--text-label-lg-font-size);
  font-weight: var(--text-label-lg-font-weight);
  line-height: var(--text-label-lg-line-height);
}

.design-system-page__scenario {
  display: grid;
  gap: var(--space-sm);
}

.design-system-page__scenario-header {
  display: grid;
  gap: 2px;
}

.design-system-page__scenario-canvas {
  width: 100%;
}

.design-system-page__scenario-canvas--none {
  width: auto;
  display: inline-flex;
  align-items: flex-start;
}

.design-system-page__scenario-canvas--card {
  padding: var(--space-sm);
  border: 1px solid var(--color-outline);
  background: var(--color-surface);
}

.design-system-page__scenario-canvas--padded {
  padding: var(--space-md);
}

.design-system-page__scenario-canvas--full-width {
  width: 100%;
}

.design-system-page__scenario-canvas--narrow {
  max-width: 320px;
}

.design-system-page__scenario-canvas--medium {
  max-width: 560px;
}

.design-system-page__scenario-canvas--wide {
  max-width: 100%;
}

@media (max-width: 960px) {
  .design-system-page__container {
    margin-left: calc(var(--space-nav-collapsed) + var(--space-page-inline));
  }
}

@media (max-width: 720px) {
  .design-system-page__nav-shell {
    width: var(--space-nav-collapsed);
  }

  .design-system-page__container {
    margin-left: calc(var(--space-nav-collapsed) + var(--space-page-inline));
    width: 100%;
  }
}
</style>
