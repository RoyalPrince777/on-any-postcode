(() => {
  "use strict";

  const heading = document.querySelector("#food-fact-title");
  const copy = document.querySelector("#food-fact-copy");
  const areaShapes = Array.from(document.querySelectorAll("[data-body-area]"));
  const areaButtons = Array.from(document.querySelectorAll("[data-area-button]"));
  const foodButtons = Array.from(document.querySelectorAll("[data-food]"));

  if (!heading || !copy || areaButtons.length === 0) return;

  const areas = new Map(
    areaButtons.map((button) => [
      button.dataset.areaButton,
      {
        name: button.dataset.areaName || "Body area",
        summary: button.dataset.areaSummary || "",
      },
    ]),
  );

  function selectArea(areaId, foodButton = null) {
    const area = areas.get(areaId);
    if (!area) return;

    areaShapes.forEach((shape) => {
      shape.classList.toggle("is-active", shape.dataset.bodyArea === areaId);
    });
    areaButtons.forEach((button) => {
      button.setAttribute(
        "aria-pressed",
        String(button.dataset.areaButton === areaId),
      );
    });
    foodButtons.forEach((button) => {
      button.setAttribute("aria-pressed", String(button === foodButton));
    });

    if (foodButton) {
      const foodName = foodButton.dataset.foodName || "Vegetable";
      const nutrients = foodButton.dataset.foodNutrients || "Nutrients";
      heading.textContent = `${foodName} → ${area.name}`;
      copy.textContent = `${nutrients}. ${area.summary}`;
    } else {
      heading.textContent = area.name;
      copy.textContent = area.summary;
    }
  }

  areaShapes.forEach((shape) => {
    const activate = () => selectArea(shape.dataset.bodyArea);
    shape.addEventListener("click", activate);
    shape.addEventListener("keydown", (event) => {
      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault();
        activate();
      }
    });
  });

  areaButtons.forEach((button) => {
    button.addEventListener("click", () => selectArea(button.dataset.areaButton));
  });

  foodButtons.forEach((button) => {
    button.addEventListener("click", () => {
      selectArea(button.dataset.foodArea, button);
    });
  });
})();
