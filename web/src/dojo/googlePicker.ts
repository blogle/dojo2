type PickerDocument = {
  id?: string;
  name?: string;
};

type PickerView = {
  setIncludeFolders(value: boolean): PickerView;
  setSelectFolderEnabled(value: boolean): PickerView;
  setMimeTypes(value: string): PickerView;
};

type PickerInstance = {
  setVisible(value: boolean): void;
};

type PickerCallback = (data: {
  action?: string;
  docs?: PickerDocument[];
}) => void;

type PickerNamespace = {
  Action: {
    CANCEL: string;
    PICKED: string;
  };
  DocsView: new (viewId: string) => PickerView;
  PickerBuilder: new () => {
    setDeveloperKey(value: string): {
      setAppId(value: string): {
        setOAuthToken(value: string): {
          addView(value: PickerView): {
            setCallback(value: PickerCallback): { build(): PickerInstance };
          };
        };
      };
    };
  };
  ViewId: { FOLDERS: string };
};

type GoogleApi = {
  load(name: string, options: { callback: () => void }): void;
};

declare global {
  interface Window {
    gapi?: GoogleApi;
    google?: { picker?: PickerNamespace };
  }
}

let pickerApiPromise: Promise<PickerNamespace> | null = null;

export async function openGoogleDriveFolderPicker(
  accessToken: string,
  pickerApiKey: string,
  pickerAppId: number,
): Promise<{ id: string; name: string } | null> {
  const picker = await loadPickerApi();
  const view = new picker.DocsView(picker.ViewId.FOLDERS)
    .setIncludeFolders(true)
    .setSelectFolderEnabled(true)
    .setMimeTypes("application/vnd.google-apps.folder");

  return new Promise((resolve, reject) => {
    let settled = false;
    const finish = (value: { id: string; name: string } | null): void => {
      if (settled) return;
      settled = true;
      resolve(value);
    };

    try {
      const pickerInstance = new picker.PickerBuilder()
        .setDeveloperKey(pickerApiKey)
        .setAppId(String(pickerAppId))
        .setOAuthToken(accessToken)
        .addView(view)
        .setCallback((data) => {
          if (data.action === picker.Action.CANCEL) {
            finish(null);
            return;
          }
          if (data.action !== picker.Action.PICKED) return;
          const document = data.docs?.[0];
          if (document?.id && document.name) {
            finish({ id: document.id, name: document.name });
          } else {
            reject(new Error("Google Picker returned an incomplete folder."));
          }
        })
        .build();
      pickerInstance.setVisible(true);
    } catch (error) {
      reject(error);
    }
  });
}

function loadPickerApi(): Promise<PickerNamespace> {
  if (window.google?.picker) return Promise.resolve(window.google.picker);
  if (pickerApiPromise) return pickerApiPromise;

  pickerApiPromise = new Promise((resolve, reject) => {
    const script = document.createElement("script");
    script.src = "https://apis.google.com/js/api.js";
    script.async = true;
    script.onload = () => {
      if (!window.gapi) {
        reject(new Error("Google Picker API failed to load."));
        return;
      }
      window.gapi.load("picker", {
        callback: () => {
          if (window.google?.picker) {
            resolve(window.google.picker);
          } else {
            reject(new Error("Google Picker API failed to initialize."));
          }
        },
      });
    };
    script.onerror = () =>
      reject(new Error("Google Picker API failed to load."));
    document.head.appendChild(script);
  });
  return pickerApiPromise;
}
