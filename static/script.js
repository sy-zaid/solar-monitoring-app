// console.log("🔋 Solar Monitor JavaScript loaded");

// Operating mode mapping
const operatingModes = {
  "000": { text: "Power On", class: "power-on", icon: "fas fa-power-off" },
  "001": { text: "Standby", class: "standby-mode", icon: "fas fa-pause" },
  110: {
    text: "Solar & Battery Mode",
    class: "solar-mode",
    icon: "fas fa-bolt",
  },
  "010": {
    text: "Battery Mode",
    class: "battery-mode",
    icon: "fas fa-battery-full",
  },
  101: {
    text: "K-Electric Mode",
    class: "ke-mode",
    icon: "fas fa-exclamation-triangle",
  },
};

let countdownInterval;

// Update current time
function updateCurrentTime() {
  const now = new Date();
  const timeString = now.toLocaleString("en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    hour12: true,
  });

  const currentTimeElement = document.getElementById("currentTime");
  if (currentTimeElement) {
    currentTimeElement.textContent = timeString;
  }
}

// Countdown timer for auto-refresh
function startCountdown() {
  let seconds = 2;
  const countdownElement = document.getElementById("countdown");

  if (countdownInterval) {
    clearInterval(countdownInterval);
  }

  countdownInterval = setInterval(() => {
    seconds--;
    if (countdownElement) {
      countdownElement.textContent = seconds;
    }

    if (seconds <= 0) {
      seconds = 5;
      fetchData();
    }
  }, 1000);
}

// Fetch updated data from server
async function fetchData() {
  try {
    // console.log("🔄 Fetching data from /api/data...");
    const response = await fetch("/api/data");
    const data = await response.json();

    // console.log("✅ Data received, updating dashboard...", data);
    updateDashboard(data);
    updateAllStatusOnRefresh(data);
    document.getElementById(
      "battery_capacity"
    ).textContent = `${updateBatteryPercentage(data.battery_voltage)}%`;
    // ✅ Make sure data.timestamp exists and is a valid date
    if (data.timestamp) {
      const lastUpdateTime = new Date(data.timestamp);
      const status = checkConnection(new Date(), lastUpdateTime);
      updateElementTextContent("lastReadingTime", status);
    } else {
      updateElementTextContent("lastReadingTime", "⚠️ Missing timestamp");
    }
  } catch (error) {
    console.error("❌ Error fetching data:", error);
  }
}

const checkConnection = (currentTime, lastUpdateTime) => {
  const difference = (currentTime - lastUpdateTime) / 1000;
  const body = document.body;

  // Reset any previous animation classes
  body.classList.remove("pulse-red", "pulse-yellow");

  if (difference >= 50) {
    body.style.backgroundColor = "red";
    body.classList.add("pulse-red");
    return "Connection Lost";
  } else if (difference >= 30) {
    body.style.backgroundColor = "yellow";
    body.classList.add("pulse-yellow");
    return "Slow Connection";
  } else {
    body.style.background =
      "linear-gradient(135deg, var(--background) 0%, #1e293b 100%)";
    return "Connected";
  }
};

// Update dashboard with new data
function updateDashboard(data) {
  // console.log("🔄 Starting dashboard update...");

  // AC Output Section
  updateElementValue("ac_output_power", data.ac_output_power, "W");
  updateElementValue("output_apparent_power", data.output_apparent_power, "VA");
  updateElementValue("load_percentage", data.load_percentage, "");
  updateElementValue(
    "load_ampere",
    parseFloat((data.ac_output_power / data.ac_output_voltage).toFixed(2)),
    "A"
  );
  updateElementValue("ac_output_voltage", data.ac_output_voltage, "V");
  updateElementTextContent(
    "ac_output_frequency",
    data.ac_output_frequency + " Hz"
  );

  // Solar Production Section
  updateElementValue("pv_power", data.pv_power, "W");
  updateElementValue("pv_voltage", data.pv_voltage, "V");
  updateElementValue("pv_charging_power", data.pv_charging_power, "A");

  // Battery Status Section
  updateElementValue("battery_capacity", data.battery_capacity, "%");
  updateElementValue("battery_voltage", data.battery_voltage, "V");
  updateElementTextContent(
    "battery_charging_current",
    data.battery_charging_current + "A"
  );
  updateElementTextContent(
    "battery_discharge_current",
    data.battery_discharge_current + "A"
  );
  updateElementValue("heat_sink_temp", data.heat_sink_temp, "°C");

  // Grid Status Section
  updateElementValue("grid_voltage", data.grid_voltage, "V");
  updateElementTextContent("grid_frequency", data.grid_frequency + " Hz");
  updateElementValue("bus_voltage", data.bus_voltage, "V");

  // System Information Section
  updateElementTextContent("status_code", data.device_status);
  updateElementTextContent("status_bits", data.status_bits);
  updateElementTextContent("status_binary", "Binary: " + data.status_bits);
  updateElementTextContent("fan_battery_offset", data.fan_battery_offset);
  updateElementTextContent("eeprom_fw", data.eeprom_fw);
  updateElementTextContent("reserved", data.reserved);

  // Timestamps

  updateElementTextContent("lastUpdateTime", data.last_updated);

  // Operating Mode
  updateOperatingMode(data.device_status);

  
  // console.log("✅ Dashboard update completed");
}

// Update all statuses at once
function updateAllStatusOnRefresh(data) {
  // For flow lines
  const fd1 = document.getElementById("flow-dot-1");
  const fd2 = document.getElementById("flow-dot-2");
  const fd3 = document.getElementById("flow-dot-3");
  const fd4 = document.getElementById("flow-dot-4");
  const fd5 = document.getElementById("flow-dot-5");

  const forlooplist = [fd1, fd2, fd3, fd4, fd5];
  forlooplist.forEach((elem) => {
    elem.classList.remove("flow-dot");
    // console.log(`FD ${elem} -----------`, elem.classList);
  });

  //   For Battery Charge/Discharge State
  const charging = document.getElementById("arrow-down");
  const discharging = document.getElementById("arrow-up");

  charging.classList.add("hidden");
  discharging.classList.add("hidden");

  if (data.battery_charging_current > 0) {
    charging.classList.remove("hidden");
  }
  if (data.battery_discharge_current > 0) {
    discharging.classList.remove("hidden");
  }

  if (data.pv_power > 0) {
    fd1.classList.add("flow-dot");
  }
  if (data.ac_output_power > 0) {
    fd2.classList.add("flow-dot");
  }
  if (data.grid_voltage > 0) {
    fd3.classList.add("flow-dot");
  }
  if (data.battery_discharge_current > 0) {
    fd4.classList.add("flow-dot");
    // console.log("CLASS LIST", fd4.classList, fd4.id);
  }
  if (data.battery_charging_current > 0) {
    fd5.classList.add("flow-dot");
    // console.log("CLASS LIST", fd5.classList, fd5.id);
  }
}

function updateBatteryPercentage(voltage) {
  const FULL_VOLTAGE = 28.6; // bulk charge
  const FLOAT_VOLTAGE = 27.0; // float voltage (around 90-95%)
  const EMPTY_VOLTAGE = 21.0; // cutoff voltage

  // Clamp voltage to expected range
  if (voltage >= FULL_VOLTAGE) return 100;
  if (voltage <= EMPTY_VOLTAGE) return 0;

  // Approximate curve (LiFePO4 voltage vs SOC, scaled to your 24V system)
  const voltageToPercent = [
    [21.0, 0],
    [23.0, 10],
    [25.0, 40],
    [26.0, 70],
    [27.0, 90],
    [28.6, 100],
  ];

  // Find where the voltage lies between two points
  for (let i = 0; i < voltageToPercent.length - 1; i++) {
    const [v1, p1] = voltageToPercent[i];
    const [v2, p2] = voltageToPercent[i + 1];
    if (voltage >= v1 && voltage <= v2) {
      // Linear interpolation between points
      return Math.round(p1 + ((voltage - v1) / (v2 - v1)) * (p2 - p1));
    }
  }

  return 0; // fallback
}
// Update element with value and unit (for card values)
function updateElementValue(elementId, value, unit) {
  const element = document.getElementById(elementId);
  if (element) {
    element.innerHTML = `${parseFloat(
      value
    )} <span class="unit">${unit}</span>`;
    highlightUpdate(element);
    // console.log(`✅ Updated ${elementId}: ${value}${unit}`);
  } else {
    // console.log(`❌ Element not found: ${elementId}`);
  }
}

// Update element text content (for plain text)
function updateElementTextContent(elementId, text) {
  const element = document.getElementById(elementId);
  if (element) {
    element.textContent = text;
    highlightUpdate(element);
    // console.log(`✅ Updated ${elementId}: ${text}`);
  } else {
    // console.log(`❌ Element not found: ${elementId}`);
  }
}

// Update operating mode
function updateOperatingMode(deviceStatus) {
  const mode = operatingModes[deviceStatus] || {
    text: "Unknown",
    class: "standby-mode",
    icon: "fas fa-question",
  };

  const modeElement = document.getElementById("operatingMode");
  const statusDescription = document.getElementById("statusDescription");

  if (modeElement) {
    modeElement.className = "status-badge " + mode.class;
    modeElement.innerHTML = `<i class="${mode.icon}"></i><span>${mode.text}</span>`;
    // console.log(`✅ Updated operating mode: ${mode.text}`);
  }

  if (statusDescription) {
    statusDescription.textContent = getStatusDescription(deviceStatus);
  }
}

// Get status description
function getStatusDescription(status) {
  const descriptions = {
    "000": "System is powered on and initializing",
    "001": "System in standby mode, ready for activation",
    110: "Operating from Solar Grid and Battery power",
    "000": "Operating from battery backup power",
    101: "Operating from AC",
  };
  return descriptions[status] || "Unknown operating state";
}

// Highlight element when updated
function highlightUpdate(element) {
  element.classList.add("value-updated");
  setTimeout(() => {
    element.classList.remove("value-updated");
  }, 1000);
}


// Debug function to check ALL elements
function checkAllElements() {
  // console.log("🔍 CHECKING ALL ELEMENTS:");

  const allElements = [
    "ac_output_power",
    "output_apparent_power",
    "load_percentage",
    "ac_output_voltage",
    "ac_output_frequency",
    "pv_power",
    "pv_voltage",
    "pv_charging_power",
    "battery_capacity",
    "battery_voltage",
    "battery_charging_current",
    "battery_discharge_current",
    "heat_sink_temp",
    "grid_voltage",
    "grid_frequency",
    "bus_voltage",
    "status_code",
    "status_bits",
    "status_binary",
    "fan_battery_offset",
    "eeprom_fw",
    "reserved",
    "lastReadingTime",
    "lastUpdateTime",
    "operatingMode",
    "statusDescription",
  ];

  allElements.forEach((id) => {
    const element = document.getElementById(id);
    // console.log(
    //   `${element ? "✅" : "❌"} ${id}:`,
    //   element ? `FOUND` : "NOT FOUND"
    // );
  });
}

// Initialize everything when page loads
document.addEventListener("DOMContentLoaded", function () {
  // console.log("🚀 DOM Content Loaded - Solar Monitor Initialized");

  updateCurrentTime();
  startCountdown();

  // Update time every second
  setInterval(updateCurrentTime, 1000);

  // Check elements after page loads
  setTimeout(() => {
    checkAllElements();
    // console.log(
    //   "💡 Tip: Use checkAllElements() in console to see which elements exist"
    // );
    // console.log("💡 Tip: Use fetchData() in console to manually refresh data");
  }, 1000);
});

// Add CSS for animations
const style = document.createElement("style");
style.textContent = `
    @keyframes slideIn {
        from {
            transform: translateX(100%);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
    
    .value-updated {
        animation: valueUpdate 1s ease-in-out;
    }
    

`;
document.head.appendChild(style);
