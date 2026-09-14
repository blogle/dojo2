import { afterEach, beforeEach, describe, expect, it } from "vitest";

import { openGoogleDriveFolderPicker } from "../src/dojo/googlePicker";

describe("openGoogleDriveFolderPicker", () => {
  let action = "cancel";
  let builder: {
    developerKey: string;
    appId: string;
    accessToken: string;
    includeFolders: boolean;
    selectFolder: boolean;
    mimeTypes: string;
  };

  beforeEach(() => {
    builder = {
      developerKey: "",
      appId: "",
      accessToken: "",
      includeFolders: false,
      selectFolder: false,
      mimeTypes: "",
    };
    class FakeDocsView {
      setIncludeFolders(value: boolean) {
        builder.includeFolders = value;
        return this;
      }

      setSelectFolderEnabled(value: boolean) {
        builder.selectFolder = value;
        return this;
      }

      setMimeTypes(value: string) {
        builder.mimeTypes = value;
        return this;
      }
    }
    class FakePickerBuilder {
      private callback: ((data: unknown) => void) | undefined;

      setDeveloperKey(value: string) {
        builder.developerKey = value;
        return this;
      }

      setAppId(value: string) {
        builder.appId = value;
        return this;
      }

      setOAuthToken(value: string) {
        builder.accessToken = value;
        return this;
      }

      addView() {
        return this;
      }

      setCallback(callback: (data: unknown) => void) {
        this.callback = callback;
        return this;
      }

      build() {
        return {
          setVisible: () => {
            this.callback?.(
              action === "picked"
                ? {
                    action: "picked",
                    docs: [{ id: "folder-id", name: "Folder name" }],
                  }
                : { action: "cancel" },
            );
          },
        };
      }
    }

    vi.stubGlobal("google", {
      picker: {
        Action: { CANCEL: "cancel", PICKED: "picked" },
        DocsView: FakeDocsView,
        PickerBuilder: FakePickerBuilder,
        ViewId: { FOLDERS: "folders" },
      },
    });
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("resolves null when the user cancels", async () => {
    const selected = await openGoogleDriveFolderPicker("access", "key", 123);

    expect(selected).toBeNull();
  });

  it("returns the selected folder and configures folder-only access", async () => {
    action = "picked";

    const selected = await openGoogleDriveFolderPicker("access", "key", 123);

    expect(selected).toEqual({ id: "folder-id", name: "Folder name" });
    expect(builder).toEqual({
      developerKey: "key",
      appId: "123",
      accessToken: "access",
      includeFolders: true,
      selectFolder: true,
      mimeTypes: "application/vnd.google-apps.folder",
    });
  });
});
