import type { ComponentFixtureSet } from "@/dojo/components/fixtures";

import button from "@/dojo/components/actions/Button.fixtures";
import dropdownButton from "@/dojo/components/actions/DropdownButton.fixtures";
import introCallout from "@/dojo/components/content/IntroCallout.fixtures";
import metricStrip from "@/dojo/components/data/MetricStrip.fixtures";
import pageHeader from "@/dojo/components/data/PageHeader.fixtures";
import periodSelector from "@/dojo/components/data/PeriodSelector.fixtures";
import keyValueList from "@/dojo/components/display/KeyValueList.fixtures";
import progressBar from "@/dojo/components/display/ProgressBar.fixtures";
import progressRing from "@/dojo/components/display/ProgressRing.fixtures";
import stateBadge from "@/dojo/components/display/StateBadge.fixtures";
import tooltip from "@/dojo/components/display/Tooltip.fixtures";
import historicalBanner from "@/dojo/components/feedback/HistoricalBanner.fixtures";
import persistentWarningBanner from "@/dojo/components/feedback/PersistentWarningBanner.fixtures";
import previewBox from "@/dojo/components/feedback/PreviewBox.fixtures";
import reorderModeBanner from "@/dojo/components/feedback/ReorderModeBanner.fixtures";
import colorSwatchGrid from "@/dojo/components/foundations/ColorSwatchGrid.fixtures";
import radiusScale from "@/dojo/components/foundations/RadiusScale.fixtures";
import spacingScale from "@/dojo/components/foundations/SpacingScale.fixtures";
import typographySpecimen from "@/dojo/components/foundations/TypographySpecimen.fixtures";
import currencyField from "@/dojo/components/forms/CurrencyField.fixtures";
import datePicker from "@/dojo/components/forms/DatePicker.fixtures";
import radioGroup from "@/dojo/components/forms/RadioGroup.fixtures";
import selectField from "@/dojo/components/forms/SelectField.fixtures";
import slider from "@/dojo/components/forms/Slider.fixtures";
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
import goalEditor from "@/dojo/components/budget/GoalEditor.fixtures";

export const fixtureRegistry: Record<string, ComponentFixtureSet> = {
  "actions/Button.fixtures.ts": button,
  "actions/DropdownButton.fixtures.ts": dropdownButton,
  "content/IntroCallout.fixtures.ts": introCallout,
  "data/MetricStrip.fixtures.ts": metricStrip,
  "data/PageHeader.fixtures.ts": pageHeader,
  "data/PeriodSelector.fixtures.ts": periodSelector,
  "display/KeyValueList.fixtures.ts": keyValueList,
  "display/ProgressBar.fixtures.ts": progressBar,
  "display/ProgressRing.fixtures.ts": progressRing,
  "display/StateBadge.fixtures.ts": stateBadge,
  "display/Tooltip.fixtures.ts": tooltip,
  "feedback/HistoricalBanner.fixtures.ts": historicalBanner,
  "feedback/PersistentWarningBanner.fixtures.ts": persistentWarningBanner,
  "feedback/PreviewBox.fixtures.ts": previewBox,
  "feedback/ReorderModeBanner.fixtures.ts": reorderModeBanner,
  "foundations/ColorSwatchGrid.fixtures.ts": colorSwatchGrid,
  "foundations/RadiusScale.fixtures.ts": radiusScale,
  "foundations/SpacingScale.fixtures.ts": spacingScale,
  "foundations/TypographySpecimen.fixtures.ts": typographySpecimen,
  "forms/CurrencyField.fixtures.ts": currencyField,
  "forms/DatePicker.fixtures.ts": datePicker,
  "forms/RadioGroup.fixtures.ts": radioGroup,
  "forms/SelectField.fixtures.ts": selectField,
  "forms/Slider.fixtures.ts": slider,
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
  "budget/GoalEditor.fixtures.ts": goalEditor,
};
