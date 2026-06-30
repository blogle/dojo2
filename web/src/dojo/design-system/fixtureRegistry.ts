import type { ComponentFixtureSet } from "@/dojo/components/fixtures";

import introCallout from "@/dojo/components/content/IntroCallout.fixtures";
import colorSwatchGrid from "@/dojo/components/foundations/ColorSwatchGrid.fixtures";
import radiusScale from "@/dojo/components/foundations/RadiusScale.fixtures";
import spacingScale from "@/dojo/components/foundations/SpacingScale.fixtures";
import typographySpecimen from "@/dojo/components/foundations/TypographySpecimen.fixtures";
import divider from "@/dojo/components/layout/Divider.fixtures";
import grid from "@/dojo/components/layout/Grid.fixtures";
import inline from "@/dojo/components/layout/Inline.fixtures";
import stack from "@/dojo/components/layout/Stack.fixtures";
import surface from "@/dojo/components/layout/Surface.fixtures";
import navigationRail from "@/dojo/components/navigation/NavigationRail.fixtures";

export const fixtureRegistry: Record<string, ComponentFixtureSet> = {
  "content/IntroCallout.fixtures.ts": introCallout,
  "foundations/ColorSwatchGrid.fixtures.ts": colorSwatchGrid,
  "foundations/RadiusScale.fixtures.ts": radiusScale,
  "foundations/SpacingScale.fixtures.ts": spacingScale,
  "foundations/TypographySpecimen.fixtures.ts": typographySpecimen,
  "layout/Divider.fixtures.ts": divider,
  "layout/Grid.fixtures.ts": grid,
  "layout/Inline.fixtures.ts": inline,
  "layout/Stack.fixtures.ts": stack,
  "layout/Surface.fixtures.ts": surface,
  "navigation/NavigationRail.fixtures.ts": navigationRail,
};
