import type { Component } from "vue";

export type FixtureViewport = "narrow" | "medium" | "wide";
export type FixtureContainer = "none" | "card" | "padded" | "full-width";

export interface FixturePresentation {
  viewport?: FixtureViewport;
  container?: FixtureContainer;
}

export interface ComponentFixtureScenario<
  Props extends object = Record<string, unknown>,
> {
  name: string;
  description?: string;
  props?: Partial<Props>;
  slots?: Record<string, string>;
  notes?: string;
  presentation?: FixturePresentation;
}

export interface ComponentFixtureSet<
  Props extends object = Record<string, unknown>,
> {
  component: Component;
  title: string;
  description: string;
  presentation?: FixturePresentation;
  scenarios: ComponentFixtureScenario<Props>[];
}

export const defineFixtures = <Props extends object>(
  fixtures: ComponentFixtureSet<Props>,
): ComponentFixtureSet<Props> => fixtures;
