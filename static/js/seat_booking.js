document.addEventListener('DOMContentLoaded', function () {
    const seatMap = document.getElementById('seat-map');
    const selectedSeats = new Set();

    // Config variables
    const isSeatedEvent = typeof IS_SEATED !== 'undefined' ? IS_SEATED : true;
    let qty = 1;
    const maxQty = 10;

    if (!isSeatedEvent) {
        initGeneralAdmission();
    } else {
        initSeatedEvent();
    }

    function initGeneralAdmission() {
        // Find elements
        const minusBtn = document.getElementById('minus-qty');
        const addBtn = document.getElementById('add-qty');
        const qtyDisplay = document.getElementById('ticket-qty-display');

        minusBtn.onclick = () => { if (qty > 1) { qty--; updateGeneralSummary(); qtyDisplay.innerText = qty; } };
        addBtn.onclick = () => { if (qty < maxQty) { qty++; updateGeneralSummary(); qtyDisplay.innerText = qty; } };

        updateGeneralSummary();
    }

    function updateGeneralSummary() {
        const list = document.getElementById('selected-seats-list');
        const priceEl = document.getElementById('total-price');

        list.innerHTML = `<p>${qty} General Admission Ticket${qty > 1 ? 's' : ''}</p>`;
        const total = qty * PRICE_PER_SEAT;
        priceEl.innerText = `₹${total.toFixed(2)}`;
    }

    function initSeatedEvent() {
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
            if (seatMap) seatMap.appendChild(rowDiv);
            r++;
        }
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
            priceEl.innerText = '₹0.00';
            return;
        }

        list.innerHTML = `<p><strong>Seats:</strong> ${Array.from(selectedSeats).join(', ')}</p>`;
        const total = selectedSeats.size * PRICE_PER_SEAT;
        priceEl.innerText = `₹${total.toFixed(2)}`;
    }

    window.proceedToPayment = function () {
        if (!isSeatedEvent) {
            // General admission booking
            const seatsArray = [];
            for (let i = 0; i < qty; i++) {
                seatsArray.push('GEN');
            }
            submitBooking(seatsArray);
            return;
        }

        if (selectedSeats.size === 0) {
            alert('Please select at least one seat.');
            return;
        }

        submitBooking(Array.from(selectedSeats));
    };

    function submitBooking(seatsArray) {
        fetch('/book/confirm', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                event_id: EVENT_ID,
                seats: seatsArray
            })
        })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    window.location.href = `/book/pending/${data.booking_id}`;
                } else {
                    alert('Booking failed. Please try again.');
                }
            });
    }

});
