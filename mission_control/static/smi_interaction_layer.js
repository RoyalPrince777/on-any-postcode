(() => {
  "use strict";

  function bootInteractionLayer() {
    const chatbox = document.querySelector(".chatbox");
    const chatHead = document.querySelector(".chat-head");
    const form = document.getElementById("chat-form");
    const message = document.getElementById("message");
    const mic = document.getElementById("mic-button");
    const plus = document.getElementById("plus-button");
    const attachMenu = document.getElementById("attach-menu");
    const thinking = document.getElementById("thinking-level");
    const imageInput = document.getElementById("image-input");
    const imagePreview = document.getElementById("image-preview");
    const previewImg = document.getElementById("preview-img");
    const previewName = document.getElementById("preview-name");
    const status = document.getElementById("status");
    if (!chatbox || !chatHead || !form || !message || !plus || !attachMenu || !thinking || !imageInput) return;
    if (document.getElementById("interaction-strip")) return;

    const setStatus = (value) => {
      if (status) status.textContent = value;
    };

    const strip = document.createElement("nav");
    strip.id = "interaction-strip";
    strip.className = "smi-interaction-strip";
    strip.setAttribute("aria-label", "SMI interaction modes");
    strip.innerHTML = `
      <button type="button" class="smi-interaction-tab active" id="chat-mode-button" aria-pressed="true">💬 <span>Chat</span></button>
      <button type="button" class="smi-interaction-tab" id="voice-mode-button" aria-pressed="false">🎙️ <span>Voice</span></button>
      <button type="button" class="smi-interaction-tab" id="vision-button" aria-pressed="false">👁️ <span>Vision</span></button>
      <button type="button" class="smi-interaction-tab" id="faceup-button" aria-pressed="false">📹 <span>Face Up</span></button>
      <button type="button" class="smi-interaction-tab" id="screen-mode-button" aria-pressed="false">🖥️ <span>Screen</span></button>
      <button type="button" class="smi-interaction-tab" id="tools-mode-button" aria-pressed="false">📎 <span>Tools</span></button>
    `;
    (document.getElementById("thinking") || chatHead).insertAdjacentElement("afterend", strip);

    const drawer = document.createElement("section");
    drawer.id = "faceup-panel";
    drawer.className = "smi-faceup-drawer";
    drawer.hidden = true;
    drawer.setAttribute("aria-label", "Face Up visual session");
    drawer.innerHTML = `
      <div class="smi-faceup-head">
        <div><strong>📹 Face Up</strong><small>Local camera + mic session · governed visual capture</small></div>
        <button type="button" class="smi-faceup-close" id="faceup-close" aria-label="Close Face Up">×</button>
      </div>
      <video id="faceup-video" autoplay playsinline muted></video>
      <div class="smi-faceup-controls">
        <button type="button" class="tool-btn" id="faceup-camera-toggle" aria-pressed="true">📷 Camera on</button>
        <button type="button" class="tool-btn" id="faceup-mic-toggle" aria-pressed="true">🎙️ Mic on</button>
        <button type="button" class="tool-btn" id="faceup-capture">👁️ Send frame to Vision</button>
        <button type="button" class="tool-btn smi-faceup-stop" id="faceup-stop">■ End</button>
      </div>
      <div class="smi-faceup-status" id="faceup-status" aria-live="polite">Not started.</div>
      <p class="smi-faceup-truth">Continuous live SMI video participation is not certified yet. Captured frames use the existing governed Vision → SMI stream path; camera and mic remain under your device controls.</p>
    `;
    strip.insertAdjacentElement("afterend", drawer);

    const cameraInput = document.createElement("input");
    cameraInput.id = "smi-vision-camera-input";
    cameraInput.type = "file";
    cameraInput.accept = "image/png,image/jpeg,image/webp,image/gif";
    cameraInput.setAttribute("capture", "environment");
    cameraInput.hidden = true;
    form.prepend(cameraInput);

    const mediaHeading = attachMenu.querySelector(".attach-section-label");
    const insertTool = (id, label) => {
      const button = document.createElement("button");
      button.type = "button";
      button.className = "attach-option";
      button.id = id;
      button.textContent = label;
      if (mediaHeading && mediaHeading.nextSibling) {
        mediaHeading.parentNode.insertBefore(button, mediaHeading.nextSibling);
      } else {
        attachMenu.prepend(button);
      }
      return button;
    };
    const faceupMenu = insertTool("faceup-menu-button", "📹 Face Up");
    const screenMenu = insertTool("screen-menu-button", "🖥️ Screen Intelligence");
    const cameraMenu = insertTool("camera-menu-button", "👁️ SMI Vision · camera");

    const previousLevel = thinking.value || "auto";
    const modeOptions = [
      ["auto", "Auto"],
      ["manual", "Manual"],
      ["instant", "3"],
      ["think", "7"],
      ["deep_dive", "21"],
      ["war_room", "War Room"],
    ];
    thinking.replaceChildren(...modeOptions.map(([value, label]) => {
      const option = document.createElement("option");
      option.value = value;
      option.textContent = label;
      return option;
    }));
    thinking.value = modeOptions.some(([value]) => value === previousLevel) ? previousLevel : "auto";
    thinking.setAttribute("aria-label", "Intelligence selector: Auto, Manual, 3, 7, 21 or War Room");

    const tabs = Array.from(strip.querySelectorAll(".smi-interaction-tab"));
    const activate = (id) => {
      tabs.forEach((tab) => {
        const active = tab.id === id;
        tab.classList.toggle("active", active);
        tab.setAttribute("aria-pressed", String(active));
      });
    };

    function applyVisionImage(dataUrl, name) {
      selectedImage = dataUrl;
      if (previewImg) previewImg.src = selectedImage;
      if (previewName) previewName.textContent = name;
      if (imagePreview) imagePreview.classList.add("show");
      setStatus(name + " ready · send to SMI when you choose");
    }

    cameraInput.addEventListener("change", () => {
      const file = cameraInput.files && cameraInput.files[0];
      if (!file) return;
      if (file.size > 5 * 1024 * 1024) {
        setStatus("Vision capture must be 5 MB or smaller");
        cameraInput.value = "";
        return;
      }
      const reader = new FileReader();
      reader.onload = () => applyVisionImage(String(reader.result || ""), "SMI Vision camera capture");
      reader.onerror = () => setStatus("Vision capture could not be read.");
      reader.readAsDataURL(file);
    });

    async function captureScreen() {
      activate("screen-mode-button");
      if (!navigator.mediaDevices || !navigator.mediaDevices.getDisplayMedia) {
        setStatus("Screen Intelligence is unavailable in this browser.");
        return;
      }
      let stream = null;
      try {
        setStatus("Choose a screen or app to share with SMI…");
        stream = await navigator.mediaDevices.getDisplayMedia({video: true, audio: false});
        const video = document.createElement("video");
        video.srcObject = stream;
        video.muted = true;
        video.playsInline = true;
        await video.play();
        if (video.readyState < 2) {
          await new Promise((resolve) => video.addEventListener("loadeddata", resolve, {once: true}));
        }
        const width = Math.max(1, video.videoWidth);
        const height = Math.max(1, video.videoHeight);
        const scale = Math.min(1, 1280 / width);
        const canvas = document.createElement("canvas");
        canvas.width = Math.max(1, Math.round(width * scale));
        canvas.height = Math.max(1, Math.round(height * scale));
        canvas.getContext("2d").drawImage(video, 0, 0, canvas.width, canvas.height);
        applyVisionImage(canvas.toDataURL("image/jpeg", 0.82), "Screen Intelligence capture");
      } catch (error) {
        if (error && (error.name === "NotAllowedError" || error.name === "AbortError")) {
          setStatus("Screen share cancelled or blocked by device permission.");
        } else {
          setStatus("Screen Intelligence capture failed safely.");
        }
      } finally {
        if (stream) stream.getTracks().forEach((track) => track.stop());
      }
    }

    let faceUpStream = null;
    const faceVideo = drawer.querySelector("#faceup-video");
    const faceStatus = drawer.querySelector("#faceup-status");
    const faceCamera = drawer.querySelector("#faceup-camera-toggle");
    const faceMic = drawer.querySelector("#faceup-mic-toggle");

    const stopFaceUp = () => {
      if (faceUpStream) faceUpStream.getTracks().forEach((track) => track.stop());
      faceUpStream = null;
      faceVideo.srcObject = null;
      drawer.hidden = true;
      faceStatus.textContent = "Ended.";
      faceCamera.setAttribute("aria-pressed", "true");
      faceMic.setAttribute("aria-pressed", "true");
      faceCamera.textContent = "📷 Camera on";
      faceMic.textContent = "🎙️ Mic on";
      activate("chat-mode-button");
      setStatus("Face Up ended by Human Authority.");
    };

    async function startFaceUp() {
      activate("faceup-button");
      drawer.hidden = false;
      if (faceUpStream) return;
      if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        faceStatus.textContent = "Camera/mic access is unavailable in this browser.";
        setStatus("Face Up is unavailable in this browser.");
        return;
      }
      try {
        faceStatus.textContent = "Requesting camera and microphone permission…";
        faceUpStream = await navigator.mediaDevices.getUserMedia({
          video: {facingMode: "user"},
          audio: true,
        });
        faceVideo.srcObject = faceUpStream;
        await faceVideo.play();
        faceStatus.textContent = "Local Face Up session active. Nothing is sent until you capture and send.";
        setStatus("Face Up active · camera/mic under your control");
      } catch (error) {
        faceUpStream = null;
        faceVideo.srcObject = null;
        faceStatus.textContent = "Camera/mic permission blocked or unavailable.";
        setStatus("Face Up did not start.");
      }
    }

    faceCamera.addEventListener("click", () => {
      if (!faceUpStream) return;
      const track = faceUpStream.getVideoTracks()[0];
      if (!track) return;
      track.enabled = !track.enabled;
      faceCamera.setAttribute("aria-pressed", String(track.enabled));
      faceCamera.textContent = track.enabled ? "📷 Camera on" : "📷 Camera off";
    });
    faceMic.addEventListener("click", () => {
      if (!faceUpStream) return;
      const track = faceUpStream.getAudioTracks()[0];
      if (!track) return;
      track.enabled = !track.enabled;
      faceMic.setAttribute("aria-pressed", String(track.enabled));
      faceMic.textContent = track.enabled ? "🎙️ Mic on" : "🎙️ Mic off";
    });
    drawer.querySelector("#faceup-capture").addEventListener("click", () => {
      if (!faceUpStream || !faceVideo.videoWidth) {
        faceStatus.textContent = "Start Face Up before capturing a frame.";
        return;
      }
      const width = faceVideo.videoWidth;
      const height = faceVideo.videoHeight;
      const scale = Math.min(1, 1280 / width);
      const canvas = document.createElement("canvas");
      canvas.width = Math.max(1, Math.round(width * scale));
      canvas.height = Math.max(1, Math.round(height * scale));
      canvas.getContext("2d").drawImage(faceVideo, 0, 0, canvas.width, canvas.height);
      applyVisionImage(canvas.toDataURL("image/jpeg", 0.84), "Face Up Vision frame");
      faceStatus.textContent = "Frame captured for governed Vision analysis. Send when ready.";
    });
    drawer.querySelector("#faceup-stop").addEventListener("click", stopFaceUp);
    drawer.querySelector("#faceup-close").addEventListener("click", stopFaceUp);

    strip.querySelector("#chat-mode-button").addEventListener("click", () => {
      activate("chat-mode-button");
      message.focus();
    });
    strip.querySelector("#voice-mode-button").addEventListener("click", () => {
      activate("voice-mode-button");
      if (mic && !mic.disabled) mic.click();
      else setStatus("Voice input is unavailable right now.");
    });
    strip.querySelector("#vision-button").addEventListener("click", () => {
      activate("vision-button");
      cameraInput.click();
    });
    strip.querySelector("#faceup-button").addEventListener("click", startFaceUp);
    strip.querySelector("#screen-mode-button").addEventListener("click", captureScreen);
    strip.querySelector("#tools-mode-button").addEventListener("click", () => {
      activate("tools-mode-button");
      plus.click();
      if (!attachMenu.classList.contains("show")) activate("chat-mode-button");
    });

    cameraMenu.addEventListener("click", () => {
      attachMenu.classList.remove("show");
      cameraInput.click();
      activate("vision-button");
    });
    screenMenu.addEventListener("click", () => {
      attachMenu.classList.remove("show");
      captureScreen();
    });
    faceupMenu.addEventListener("click", () => {
      attachMenu.classList.remove("show");
      startFaceUp();
    });

    thinking.addEventListener("change", () => {
      const label = thinking.options[thinking.selectedIndex]?.textContent || "Auto";
      setStatus("Intelligence " + label + " selected · Human Authority remains final");
    });

    const pauseControl = document.getElementById("pause-button");
    if (pauseControl) {
      pauseControl.title = "Pause/resume the local response display. Use Stop to cancel the governed stream.";
      pauseControl.addEventListener("click", () => {
        window.setTimeout(() => {
          const paused = pauseControl.getAttribute("aria-pressed") === "true";
          setStatus(
            paused
              ? "Display paused · backend/provider work may continue until Stop"
              : "Display resumed · governed stream continues"
          );
        }, 0);
      });
    }

    window.addEventListener("pagehide", () => {
      if (faceUpStream) faceUpStream.getTracks().forEach((track) => track.stop());
    }, {once: true});
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", bootInteractionLayer, {once: true});
  } else {
    bootInteractionLayer();
  }
})();