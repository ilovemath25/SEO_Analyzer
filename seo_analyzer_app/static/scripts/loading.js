function checkStatus() {
   fetch("/check_status")
   .then(response => response.json())
   .then(data => {
      document.querySelector(".task1 .circle-status").classList.remove("loading-status");
      document.querySelector(".task1 .circle-status").classList.add("finish-status");
   });
}
setInterval(checkStatus, 500);