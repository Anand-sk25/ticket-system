document.addEventListener('DOMContentLoaded', function () {
    const seatMap = document.getElementById('seat-map');
    const selectedSeats = new Set();

    let cols = 10;
    let r = 0;
    let totalCreated = 0;
    let totalSeats = typeof TOTAL_SEATS !== 'undefined' ? TOTAL_SEATS : 48; // Default if not provided

    function getRowLabel(idx) {
        let res = "";
        while (idx >= 0) {
            res = String.fromCharCode(65 + (idx % 26)) + res;
            idx = Math.floor(idx / 26) - 1;
        }
        return res;
    }

    // Generate Seats
    while (totalCreated < totalSeats) {
        const rowDiv = document.createElement('div');
        rowDiv.className = 'seat-row';

        const rowLabel = getRowLabel(r);

        for (let c = 1; c <= cols; c++) {
            if (totalCreated >= totalSeats) break;

            const seatId = `${rowLabel}${c}`;
            const seat = document.createElement('div');
            seat.className = 'seat';
            seat.dataset.id = seatId;
            seat.innerText = '';
            seat.title = `Seat ${seatId}`;
            totalCreated++;

            // Check if seat is really booked
            if (BOOKED_SEATS.includes(seatId)) {
                seat.classList.add('booked');
            } else {
                seat.onclick = () => toggleSeat(seat);
            }

            rowDiv.appendChild(seat);
        }
        seatMap.appendChild(rowDiv);
        r++;
    }

    window.toggleSeat = function (seat) {
        if (seat.classList.contains('booked')) return;

        const seatId = seat.dataset.id;
        if (selectedSeats.has(seatId)) {
            selectedSeats.delete(seatId);
            seat.classList.remove('selected');
        } else {
            selectedSeats.add(seatId);
            seat.classList.add('selected');
        }
        updateSummary();
    };

    function updateSummary() {
        const list = document.getElementById('selected-seats-list');
        const priceEl = document.getElementById('total-price');

        if (selectedSeats.size === 0) {
            list.innerHTML = '<p>No seats selected</p>';
            priceEl.innerText = '$0.00';
            return;
        }

        list.innerHTML = `<p><strong>Seats:</strong> ${Array.from(selectedSeats).join(', ')}</p>`;
        const total = selectedSeats.size * PRICE_PER_SEAT;
        priceEl.innerText = `$${total.toFixed(2)}`;
    }

    window.proceedToPayment = function () {
        if (selectedSeats.size === 0) {
            alert('Please select at least one seat.');
            return;
        }


        fetch('/book/confirm', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                event_id: EVENT_ID,
                seats: Array.from(selectedSeats)
            })
        })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    window.location.href = `/book/ticket/${data.booking_id}`;
                } else {
                    alert('Booking failed. Please try again.');
                }
            });
    };

});
