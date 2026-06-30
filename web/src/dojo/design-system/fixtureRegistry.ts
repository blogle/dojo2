import type { ComponentFixtureSet } from "@/dojo/components/fixtures";

import button from "@/dojo/components/actions/Button.fixtures";
import dropdownButton from "@/dojo/components/actions/DropdownButton.fixtures";
import introCallout from "@/dojo/components/content/IntroCallout.fixtures";
import metricStrip from "@/dojo/components/data/MetricStrip.fixtures";
import pageHeader from "@/dojo/components/data/PageHeader.fixtures";
import periodSelector from "@/dojo/components/data/PeriodSelector.fixtures";
import stateBadge from "@/dojo/components/display/StateBadge.fixtures";
import historicalBanner from "@/dojo/components/feedback/HistoricalBanner.fixtures";
import persistentWarningBanner from "@/dojo/components/feedback/PersistentWarningBanner.fixtures";
import colorSwatchGrid from "@/dojo/components/foundations/ColorSwatchGrid.fixtures";
import radiusScale from "@/dojo/components/foundations/RadiusScale.fixtures";
import spacingScale from "@/dojo/components/foundations/SpacingScale.fixtures";
import typographySpecimen from "@/dojo/components/foundations/TypographySpecimen.fixtures";
import currencyField from "@/dojo/components/forms/CurrencyField.fixtures";
import selectField from "@/dojo/components/forms/SelectField.fixtures";
import textField from "@/dojo/components/forms/TextField.fixtures";
import divider from "@/dojo/components/layout/Divider.fixtures";
import grid from "@/dojo/components/layout/Grid.fixtures";
import inline from "@/dojo/components/layout/Inline.fixtures";
import stack from "@/dojo/components/layout/Stack.fixtures";
import surface from "@/dojo/components/layout/Surface.fixtures";
import navigationRail from "@/dojo/components/navigation/NavigationRail.fixtures";
import tabs from "@/dojo/components/navigation/Tabs.fixtures";
import formModal from "@/dojo/components/overlays/FormModal.fixtures";
import largeDetailModal from "@/dojo/components/overlays/LargeDetailModal.fixtures";
import hierarchicalCategoryTable from "@/dojo/components/tables/HierarchicalCategoryTable.fixtures";
import tableShell from "@/dojo/components/tables/TableShell.fixtures";

export const fixtureRegistry: Record<string, ComponentFixtureSet> = {
  "actions/Button.fixtures.ts": button,
  "actions/DropdownButton.fixtures.ts": dropdownButton,
  "content/IntroCallout.fixtures.ts": introCallout,
  "data/MetricStrip.fixtures.ts": metricStrip,
  "data/PageHeader.fixtures.ts": pageHeader,
  "data/PeriodSelector.fixtures.ts": periodSelector,
  "display/StateBadge.fixtures.ts": stateBadge,
  "feedback/HistoricalBanner.fixtures.ts": historicalBanner,
  "feedback/PersistentWarningBanner.fixtures.ts": persistentWarningBanner,
  "foundations/ColorSwatchGrid.fixtures.ts": colorSwatchGrid,
  "foundations/RadiusScale.fixtures.ts": radiusScale,
  "foundations/SpacingScale.fixtures.ts": spacingScale,
  "foundations/TypographySpecimen.fixtures.ts": typographySpecimen,
  "forms/CurrencyField.fixtures.ts": currencyField,
  "forms/SelectField.fixtures.ts": selectField,
  "forms/TextField.fixtures.ts": textField,
  "layout/Divider.fixtures.ts": divider,
  "layout/Grid.fixtures.ts": grid,
  "layout/Inline.fixtures.ts": inline,
  "layout/Stack.fixtures.ts": stack,
  "layout/Surface.fixtures.ts": surface,
  "navigation/NavigationRail.fixtures.ts": navigationRail,
  "navigation/Tabs.fixtures.ts": tabs,
  "overlays/FormModal.fixtures.ts": formModal,
  "overlays/LargeDetailModal.fixtures.ts": largeDetailModal,
  "tables/HierarchicalCategoryTable.fixtures.ts": hierarchicalCategoryTable,
  "tables/TableShell.fixtures.ts": tableShell,
};
