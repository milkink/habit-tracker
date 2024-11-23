// Note functions
let currentHabitId = null;

function openNoteModal(habitId) {
    currentHabitId = habitId;
    loadPreviousNotes(habitId);
    $('#habitNoteModal').modal('show');
}

function loadPreviousNotes(habitId) {
    $.get(`/habit/${habitId}/notes`, function(notes) {
        const container = $('#previousNotes');
        container.empty();
        
        notes.forEach(note => {
            container.append(`
                <div class="card mb-2">
                    <div class="card-body">
                        <p class="card-text">${note.note}</p>
                        <small class="text-muted">${note.date}</small>
                    </div>
                </div>
            `);
        });
    });
}

function handleNoteSaving() {
    $('#saveNote').click(function() {
        const note = $('#habitNote').val();
        if (note && currentHabitId) {
            $.ajax({
                url: `/habit/${currentHabitId}/notes`,
                type: 'POST',
                contentType: 'application/json',
                data: JSON.stringify({ note: note }),
                success: function(response) {
                    $('#habitNote').val('');
                    loadPreviousNotes(currentHabitId);
                    toastr.success('Note added successfully!');
                },
                error: function(error) {
                    toastr.error('Error adding note.');
                }
            });
        }
    });
}
