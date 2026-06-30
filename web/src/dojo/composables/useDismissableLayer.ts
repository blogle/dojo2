import { onBeforeUnmount, onMounted, type Ref } from "vue";

export const useDismissableLayer = (
  active: Ref<boolean>,
  root: Ref<HTMLElement | null>,
  onDismiss: () => void,
) => {
  const handlePointerDown = (event: MouseEvent) => {
    if (!active.value || !root.value) {
      return;
    }

    const target = event.target;

    if (target instanceof Node && !root.value.contains(target)) {
      onDismiss();
    }
  };

  const handleKeyDown = (event: KeyboardEvent) => {
    if (active.value && event.key === "Escape") {
      onDismiss();
    }
  };

  onMounted(() => {
    document.addEventListener("mousedown", handlePointerDown);
    document.addEventListener("keydown", handleKeyDown);
  });

  onBeforeUnmount(() => {
    document.removeEventListener("mousedown", handlePointerDown);
    document.removeEventListener("keydown", handleKeyDown);
  });
};
