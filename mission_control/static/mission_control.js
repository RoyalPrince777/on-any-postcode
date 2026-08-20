"use strict";

document.documentElement.classList.add("mission-control-enhanced");

for (const gateway of document.querySelectorAll("[data-mission-control-gateway]")) {
  gateway.dataset.ready = "true";
}
