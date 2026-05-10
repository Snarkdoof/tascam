document.addEventListener('DOMContentLoaded', () => {
    const songList = document.getElementById('song-list');
    const player = document.getElementById('audio-player');
    const npTitle = document.getElementById('np-title');
    const npArtist = document.getElementById('np-artist');
    const batchActions = document.getElementById('batch-actions');
    const btnBatchDelete = document.getElementById('btn-batch-delete');
    const selectedCountSpan = document.getElementById('selected-count');

    let clips = [];
    let selectedClipIds = new Set();

    // Fetch all clips
    fetch('/api/clips')
        .then(res => res.json())
        .then(data => {
            clips = data;
            renderGroups();
        })
        .catch(err => {
            songList.innerHTML = '<div class="error">Failed to load library</div>';
            console.error(err);
        });

    function getClipDate(clip) {
        if (clip.source_file && clip.source_file.filename) {
            const basename = clip.source_file.filename.split('/').pop();
            const match = basename.match(/^(\d{2})(\d{2})(\d{2})_/);
            if (match) {
                return `20${match[1]}-${match[2]}-${match[3]}`;
            }
        }
        return new Date(clip.created_at).toLocaleDateString('en-CA');
    }

    function formatDuration(seconds) {
        const h = Math.floor(seconds / 3600);
        const m = Math.floor((seconds % 3600) / 60);
        const s = Math.floor(seconds % 60);

        if (h > 0) {
            return `${h}:${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
        }
        return `${m}:${s.toString().padStart(2, '0')}`;
    }

    function formatTimestamp(seconds) {
        const h = Math.floor(seconds / 3600);
        const m = Math.floor((seconds % 3600) / 60);
        const s = Math.floor(seconds % 60);
        // Always show hh:mm:ss for absolute timestamp
        return `${h.toString().padStart(2, '0')}:${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
    }

    function updateBatchActions() {
        const count = selectedClipIds.size;
        selectedCountSpan.textContent = count;
        if (count > 0) {
            batchActions.classList.remove('hidden');
        } else {
            batchActions.classList.add('hidden');
        }
    }

    function renderGroups() {
        songList.innerHTML = '';
        selectedClipIds.clear();
        updateBatchActions();

        const groups = {};
        clips.forEach(clip => {
            const date = getClipDate(clip);
            if (!groups[date]) groups[date] = [];
            groups[date].push(clip);
        });

        const dates = Object.keys(groups).sort();

        dates.forEach(date => {
            const groupClips = groups[date];
            const groupDiv = document.createElement('div');
            groupDiv.className = 'date-group';

            const header = document.createElement('div');
            header.className = 'group-header';
            header.innerHTML = `
                <span class="group-title">${date}</span>
                <span class="group-count">${groupClips.length} clips</span>
            `;

            const content = document.createElement('div');
            content.className = 'group-content hidden';

            header.addEventListener('click', () => {
                content.classList.toggle('hidden');
            });

            groupClips.forEach(clip => {
                const clipEl = renderClipRow(clip);
                content.appendChild(clipEl);
            });

            groupDiv.appendChild(header);
            groupDiv.appendChild(content);
            songList.appendChild(groupDiv);
        });
    }

    function renderClipRow(clip) {
        const div = document.createElement('div');
        div.className = 'clip-row';
        div.dataset.id = clip.id;

        const songTitle = clip.song && clip.song.title ? clip.song.title : 'Unknown Song';
        const comment = clip.comment || 'Add comment...';
        const tempo = clip.tempo ? Math.round(clip.tempo) + ' BPM' : '-';

        const durationStr = formatDuration(clip.duration_seconds);
        const startStr = formatTimestamp(clip.start_seconds);

        div.innerHTML = `
            <div class="clip-main">
                <input type="checkbox" class="clip-checkbox" value="${clip.id}">
                <span class="clip-id">#${clip.id}</span>
                <div class="clip-play-btn">▶</div>
                <div class="clip-details">
                    <div class="clip-title editable" data-field="title">${songTitle}</div>
                    <div class="clip-meta">
                        <span class="timestamp" title="Start Time">@ ${startStr}</span>
                        <span class="duration" title="Duration">${durationStr}</span>
                        <span class="tempo">${tempo}</span>
                        <span class="comment editable" data-field="comment">${comment}</span>
                    </div>
                </div>
                </div>
            </div>
            <div class="clip-actions">
                <button class="btn-download" title="Download">⬇️</button>
                <button class="btn-delete" title="Delete">🗑</button>
            </div>
        `;

        // Checkbox Logic
        const checkbox = div.querySelector('.clip-checkbox');
        checkbox.addEventListener('change', (e) => {
            if (e.target.checked) {
                selectedClipIds.add(clip.id);
            } else {
                selectedClipIds.delete(clip.id);
            }
            updateBatchActions();
        });

        // Play
        div.querySelector('.clip-play-btn').addEventListener('click', (e) => {
            e.stopPropagation();
            playClip(clip);
        });

        // Download
        div.querySelector('.btn-download').addEventListener('click', (e) => {
            e.stopPropagation();
            window.location.href = `/api/clips/${clip.id}/download`;
        });

        // Delete (Single)
        div.querySelector('.btn-delete').addEventListener('click', (e) => {
            e.stopPropagation();
            if (confirm('Are you sure you want to delete this clip?')) {
                deleteClip(clip.id, div);
            }
        });

        // Inline Edit
        const titleEl = div.querySelector('.clip-title');
        const commentEl = div.querySelector('.comment');

        titleEl.addEventListener('click', (e) => handleEdit(e, clip.id, 'title'));
        commentEl.addEventListener('click', (e) => handleEdit(e, clip.id, 'comment'));

        return div;
    }

    function handleEdit(e, id, field) {
        e.stopPropagation();
        const el = e.target;
        const currentText = el.textContent === 'Add comment...' ? '' : el.textContent;

        const input = document.createElement('input');
        input.type = 'text';
        input.value = currentText;
        input.className = 'edit-input';

        el.replaceWith(input);
        input.focus();

        const save = async () => {
            const newVal = input.value;
            const newEl = document.createElement('div');
            newEl.className = el.className;
            newEl.dataset.field = field;
            newEl.textContent = newVal || (field === 'comment' ? 'Add comment...' : 'Unknown Song');
            newEl.addEventListener('click', (e) => handleEdit(e, id, field));
            input.replaceWith(newEl);

            try {
                const body = {};
                body[field] = newVal;
                await fetch(`/api/clips/${id}`, {
                    method: 'PATCH',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(body)
                });
            } catch (err) {
                console.error("Save failed", err);
                alert("Failed to save changes");
            }
        };

        input.addEventListener('blur', save);
        input.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') save();
        });
    }

    async function deleteClip(id, el) {
        try {
            await fetch(`/api/clips/${id}`, { method: 'DELETE' });
            el.remove();
            // Also remove from selection if present
            if (selectedClipIds.has(id)) {
                selectedClipIds.delete(id);
                updateBatchActions();
            }
        } catch (err) {
            console.error(err);
            alert("Failed to delete clip");
        }
    }

    // Batch Delete
    btnBatchDelete.addEventListener('click', async () => {
        if (!confirm(`Delete ${selectedClipIds.size} clips?`)) return;

        const idsToDelete = Array.from(selectedClipIds);
        try {
            const response = await fetch('/api/clips/batch-delete', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ clip_ids: idsToDelete })
            });

            const result = await response.json();
            if (result.ok) {
                // Determine approach: reload entirely or remove from DOM?
                // Reloading is safer to sync state.
                window.location.reload();
            } else {
                alert("Batch delete failed");
            }
        } catch (err) {
            console.error(err);
            alert("Error during batch delete");
        }
    });

    function playClip(clip) {
        npTitle.textContent = clip.song ? clip.song.title : `Clip ${clip.id}`;
        const durationStr = formatDuration(clip.duration_seconds);
        npArtist.textContent = `${durationStr} • ${clip.tempo ? Math.round(clip.tempo) + ' BPM' : ''}`;
        player.src = `/api/clips/${clip.id}/stream`;
        player.play();
    }
});
