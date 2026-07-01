import { parse } from "yaml";

import manifestRaw from "./manifest.yaml?raw";

export interface DesignSystemEntry {
  component: string;
  fixture: string;
}

export interface DesignSystemSection {
  id: string;
  title: string;
  description?: string;
  entries: DesignSystemEntry[];
}

export interface DesignSystemManifest {
  page_shell: {
    container_max_width: string;
    quick_nav: {
      position: string;
      icon_only: boolean;
      width?: string;
      offset?: string;
    };
    intro: {
      component: string;
      fixture: string;
    };
    section_heading_format: string;
    section_gap: string;
    section_heading_gap?: string;
  };
  sections: DesignSystemSection[];
}

const manifest = parse(manifestRaw) as DesignSystemManifest;

if (!manifest.page_shell) {
  throw new Error("design-system manifest is missing page_shell");
}

if (!Array.isArray(manifest.sections) || manifest.sections.length === 0) {
  throw new Error(
    "design-system manifest must declare at least one populated section",
  );
}

export default manifest;
