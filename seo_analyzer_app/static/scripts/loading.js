function finish(element) {
   element.classList.remove("loading-status");
   element.classList.add("finish-status");
}
function checkStatus() {
   fetch("/check_status")
   .then(response => response.json())
   .then(data => {
      if (data["task1"] === "done") finish(document.querySelector(".task1 .circle-status"));
      if (data["task2"] === "done") finish(document.querySelector(".task2 .circle-status"));
      if (data["task3"] === "done") finish(document.querySelector(".task3 .circle-status"));
   });
}
setInterval(checkStatus, 500);