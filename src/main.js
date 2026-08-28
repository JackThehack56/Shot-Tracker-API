import { getSG } from './_lib/data.js';

async function checkForRounds() {
    console.info("Checking for Un-Finished rounds...");
    const result = await fetch("http://127.0.0.1:8000/round");

    const data = await result.json();

    if (data.success) 
      document.getElementById("output").textContent = data.message; 
    else console.info("No Un-finished rounds found!");
}

document.addEventListener("DOMContentLoaded", checkForRounds);


function extractData(formElement) {
  const formData = new FormData(formElement);

  const Start = {
    lie: formData.get('lie1'),
    distance: Number(formData.get('distance1'))
  }
  const Finish = {
    lie: formData.get('lie2'),
    distance: Number(formData.get('distance2'))
  }

  return {
    hole: formData.get('hole'),
    stroke: formData.get('stroke'),
    club: formData.get('club'),
    category: formData.get('category'),
    start: Start,
    finish: Finish,
    sg: getSG(Start.lie, Start.distance, Finish.lie, Finish.distance)
  }
}


async function sendData(e) {
    console.info("Hello from sendData!")

    e.preventDefault();
    const formElem = e.target;
    const shotData = extractData(formElem);
    console.info(shotData)

    const result = await fetch(
      "http://127.0.0.1:8000/receive",
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify(shotData)
      }
    );

    const data = await result.json();
    console.log(data);
    const outputElem = document.getElementById("output");

    if (data.message != null) {
      outputElem.textContent = data.message;
    }
}


document.querySelector("form").onsubmit = sendData;