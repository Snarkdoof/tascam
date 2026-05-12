import { MCorp, TIMINGSRC } from 'https://cdn.mcorp.no/mcorp.js';

document.addEventListener('DOMContentLoaded', () => {
    // UI Elements
    const songList = document.getElementById('song-list');
    const namedSongList = document.getElementById('named-song-list');
    const player = document.getElementById('audio-player');
    const npTitle = document.getElementById('np-title');
    const npArtist = document.getElementById('np-artist');
    const npTags = document.getElementById('np-tags');
    const batchActions = document.getElementById('batch-actions');
    const btnBatchDelete = document.getElementById('btn-batch-delete');
    const selectedCountSpan = document.getElementById('selected-count');
    
    // View Navigation
    const navLibrary = document.getElementById('nav-library');
    const navSongs = document.getElementById('nav-songs');
    const libraryView = document.getElementById('library-view');
    const songsView = document.getElementById('songs-view');

    // Player Controls
    const btnPlayPause = document.getElementById('btn-play-pause');
    const btnBegin = document.getElementById('btn-begin');
    const btnSkipBack = document.getElementById('btn-skip-back');
    const btnRewind3s = document.getElementById('btn-rewind-3s');
    const loopControls = document.getElementById('loop-controls');
    const progressBar = document.getElementById('progress-bar');
    const progressFill = document.getElementById('progress-fill');
    const markerTrack = document.getElementById('marker-track');
    const currentTimeSpan = document.getElementById('current-time');
    const totalTimeSpan = document.getElementById('total-time');

    // Marker Controls
    const markerValInput = document.getElementById('marker-val');
    const btnAddMarker = document.getElementById('btn-add-marker');
    const markerList = document.getElementById('marker-list');
    const btnToggleMarkers = document.getElementById('btn-toggle-markers');
    const markerListContainer = document.querySelector('.marker-list-container');

    // State
    let clips = [];
    let namedSongs = [];
    let currentClip = null;
    let selectedClipIds = new Set();
    let loopMode = 'off';
    let loopSection = null;
    let activeLoopSegments = new Set();

    // Toggle Markers
    const markerHeader = document.querySelector('.marker-header');
    if (markerHeader) {
        markerHeader.addEventListener('click', () => {
            markerListContainer.classList.toggle('collapsed');
        });
    }

    // Timing Setup
    const to = new TIMINGSRC.TimingObject();
    const sync = new BasicMediaSync(player, to);

    // Sync UI to TimingObject
    to.on("timeupdate", () => {
        const pos = to.query().position;
        const duration = player.duration || 0;
        
        if (duration > 0) {
            const pct = (pos / duration) * 100;
            progressFill.style.width = `${pct}%`;
            currentTimeSpan.textContent = formatDuration(pos);
        }

        // Loop Logic
        if (loopMode !== 'off' && loopSection) {
            // Trigger loop if we pass the end of the section or fall before it
            if (pos >= loopSection.end - 0.05 || pos < loopSection.start - 0.1) {
                to.update({ position: loopSection.start, velocity: 1 });
            }
        }
    });

    // Fallback for when the audio element completely ends
    player.addEventListener('ended', () => {
        if (loopMode !== 'off' && loopSection) {
            to.update({ position: loopSection.start, velocity: 1 });
        }
    });

    to.on("change", () => {
        const vector = to.query();
        btnPlayPause.textContent = vector.velocity === 0 ? "Play" : "Pause";
    });

    // Navigation Buttons
    navLibrary.addEventListener('click', () => {
        navLibrary.classList.add('active');
        navSongs.classList.remove('active');
        libraryView.classList.remove('hidden');
        songsView.classList.add('hidden');
    });

    navSongs.addEventListener('click', () => {
        navSongs.classList.add('active');
        navLibrary.classList.remove('active');
        songsView.classList.remove('hidden');
        libraryView.classList.add('hidden');
        fetchNamedSongs();
    });

    // Playback Controls
    btnPlayPause.addEventListener('click', () => {
        const vel = to.query().velocity;
        to.update({ velocity: vel === 0 ? 1 : 0 });
    });

    btnBegin.addEventListener('click', () => {
        to.update({ position: 0 });
    });

    btnRewind3s.addEventListener('click', () => {
        const pos = to.query().position;
        to.update({ position: Math.max(0, pos - 3) });
    });

    btnSkipBack.addEventListener('click', () => {
        if (!currentClip || !currentClip.song || !currentClip.song.markers) return;
        
        const pos = to.query().position;
        const markers = [...currentClip.song.markers].sort((a, b) => a.start - b.start);
        
        // Find current marker
        let currentIdx = -1;
        for (let i = markers.length - 1; i >= 0; i--) {
            if (pos >= markers[i].start) {
                currentIdx = i;
                break;
            }
        }

        if (currentIdx === -1) {
            to.update({ position: 0 });
            return;
        }

        const currentMarker = markers[currentIdx];
        if (pos - currentMarker.start < 5 && currentIdx > 0) {
            // Skip to previous marker
            to.update({ position: markers[currentIdx - 1].start });
        } else {
            // Skip to start of current marker
            to.update({ position: currentMarker.start });
        }
    });

    function renderLoopControls() {
        if (!loopControls) return;
        loopControls.innerHTML = '';
        if (!currentClip) return;

        const duration = player.duration || 0;
        const markers = [...(currentClip.song?.markers || [])].sort((a, b) => a.start - b.start);

        const createBtn = (label, isActive, onClick) => {
            const btn = document.createElement('button');
            btn.className = `btn-loop-segment ${isActive ? 'active' : ''}`;
            btn.textContent = label;
            btn.title = `Loop ${label}`;
            btn.addEventListener('click', onClick);
            return btn;
        };

        const labelSpan = document.createElement('span');
        labelSpan.className = 'loop-label';
        labelSpan.textContent = 'Loop:';
        loopControls.appendChild(labelSpan);

        loopControls.appendChild(createBtn('All', loopMode === 'all', () => {
            if (loopMode === 'all') {
                loopMode = 'off';
                loopSection = null;
                activeLoopSegments.clear();
            } else {
                loopMode = 'all';
                loopSection = { start: 0, end: duration };
                activeLoopSegments.clear();
                to.update({ position: 0, velocity: 1 });
            }
            renderLoopControls();
        }));

        markers.forEach((m, idx) => {
            const end = idx < markers.length - 1 ? markers[idx+1].start : duration;
            const shortLabel = m.value.length > 8 ? m.value.substring(0, 7) + '…' : m.value;
            
            loopControls.appendChild(createBtn(shortLabel, activeLoopSegments.has(idx), () => {
                if (loopMode === 'all') {
                    loopMode = 'custom';
                    activeLoopSegments.clear();
                }

                if (activeLoopSegments.has(idx)) {
                    if (activeLoopSegments.size === 1) {
                        loopMode = 'off';
                        activeLoopSegments.clear();
                        loopSection = null;
                    } else {
                        activeLoopSegments.clear();
                        activeLoopSegments.add(idx);
                    }
                } else {
                    loopMode = 'custom';
                    if (activeLoopSegments.size === 0) {
                        activeLoopSegments.add(idx);
                    } else {
                        let min = Math.min(...activeLoopSegments, idx);
                        let max = Math.max(...activeLoopSegments, idx);
                        activeLoopSegments.clear();
                        for(let i=min; i<=max; i++) activeLoopSegments.add(i);
                    }
                }

                if (activeLoopSegments.size > 0) {
                    let minIdx = Math.min(...activeLoopSegments);
                    let maxIdx = Math.max(...activeLoopSegments);
                    let sectionStart = markers[minIdx].start;
                    let sectionEnd = maxIdx < markers.length - 1 ? markers[maxIdx+1].start : duration;
                    loopSection = { start: sectionStart, end: sectionEnd };
                    to.update({ position: sectionStart, velocity: 1 });
                }

                renderLoopControls();
            }));
        });
    }

    progressBar.addEventListener('click', (e) => {
        const rect = progressBar.getBoundingClientRect();
        const pct = (e.clientX - rect.left) / rect.width;
        const duration = player.duration || 0;
        to.update({ position: pct * duration });
    });

    // Marker Logic
    btnAddMarker.addEventListener('click', async () => {
        if (!currentClip || !currentClip.song) return;
        
        const pos = to.query().position;
        const val = markerValInput.value || `Mark ${currentClip.song.markers.length + 1}`;
        
        const newMarker = { start: pos, end: null, value: val };
        const updatedMarkers = [...(currentClip.song.markers || []), newMarker];
        
        try {
            const res = await fetch(`/api/songs/${currentClip.song.id}`, {
                method: 'PATCH',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ markers: updatedMarkers })
            });
            const updatedSong = await res.json();
            currentClip.song = updatedSong;
            markerValInput.value = '';
            // Expand list when adding a marker
            markerListContainer.classList.remove('collapsed');
            renderMarkers();
        } catch (err) {
            console.error(err);
            alert("Failed to add marker");
        }
    });

    // Fetch Initial Data
    function fetchClips() {
        fetch('/api/clips')
            .then(res => res.json())
            .then(data => {
                clips = data;
                renderGroups(songList, clips);
            })
            .catch(err => {
                songList.innerHTML = '<div class="error">Failed to load library</div>';
                console.error(err);
            });
    }

    function fetchNamedSongs() {
        fetch('/api/songs/named')
            .then(res => res.json())
            .then(data => {
                namedSongs = data;
                renderNamedSongs();
            })
            .catch(err => {
                namedSongList.innerHTML = '<div class="error">Failed to load songs</div>';
                console.error(err);
            });
    }

    // Rendering Logic
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
        if (isNaN(seconds)) return "0:00";
        const h = Math.floor(seconds / 3600);
        const m = Math.floor((seconds % 3600) / 60);
        const s = Math.floor(seconds % 60);

        if (h > 0) {
            return `${h}:${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
        }
        return `${m}:${s.toString().padStart(2, '0')}`;
    }

    function formatTimestamp(seconds) {
        if (isNaN(seconds)) return "00:00:00";
        const h = Math.floor(seconds / 3600);
        const m = Math.floor((seconds % 3600) / 60);
        const s = Math.floor(seconds % 60);
        return `${h.toString().padStart(2, '0')}:${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
    }

    function updateBatchActions() {
        const count = selectedClipIds.size;
        selectedCountSpan.textContent = count;
        batchActions.classList.toggle('hidden', count === 0);
    }

    function renderGroups(container, clipList) {
        container.innerHTML = '';
        selectedClipIds.clear();
        updateBatchActions();

        const groups = {};
        clipList.forEach(clip => {
            const date = getClipDate(clip);
            if (!groups[date]) groups[date] = [];
            groups[date].push(clip);
        });

        const dates = Object.keys(groups).sort().reverse();

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
            container.appendChild(groupDiv);
        });
    }

    function renderClipRow(clip) {
        const div = document.createElement('div');
        div.className = 'clip-row';
        div.dataset.id = clip.id;

        const songTitle = clip.song?.title || 'Unknown Song';
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
            <div class="clip-actions">
                <button class="btn-download" title="Download">⬇️</button>
                <button class="btn-delete" title="Delete">🗑</button>
            </div>
        `;

        const checkbox = div.querySelector('.clip-checkbox');
        checkbox.addEventListener('change', (e) => {
            if (e.target.checked) selectedClipIds.add(clip.id);
            else selectedClipIds.delete(clip.id);
            updateBatchActions();
        });

        div.querySelector('.clip-play-btn').addEventListener('click', (e) => {
            e.stopPropagation();
            playClip(clip);
        });

        div.querySelector('.btn-download').addEventListener('click', (e) => {
            e.stopPropagation();
            window.location.href = `/api/clips/${clip.id}/download`;
        });

        div.querySelector('.btn-delete').addEventListener('click', (e) => {
            e.stopPropagation();
            if (confirm('Delete this clip?')) deleteClip(clip.id, div);
        });

        const titleEl = div.querySelector('.clip-title');
        const commentEl = div.querySelector('.comment');

        titleEl.addEventListener('click', (e) => handleEdit(e, clip.id, 'title', clip));
        commentEl.addEventListener('click', (e) => handleEdit(e, clip.id, 'comment', clip));

        return div;
    }

    function renderNamedSongs() {
        namedSongList.innerHTML = '';
        const groups = {};
        namedSongs.forEach(song => {
            const date = new Date(song.created_at).toLocaleDateString('en-CA');
            if (!groups[date]) groups[date] = [];
            groups[date].push(song);
        });

        const dates = Object.keys(groups).sort().reverse();
        dates.forEach(date => {
            const groupSongs = groups[date];
            const groupDiv = document.createElement('div');
            groupDiv.className = 'date-group';
            
            const header = document.createElement('div');
            header.className = 'group-header';
            header.innerHTML = `<span class="group-title">${date}</span>`;
            
            const content = document.createElement('div');
            content.className = 'group-content';
            
            groupSongs.forEach(song => {
                const div = document.createElement('div');
                div.className = 'clip-row';
                div.innerHTML = `
                    <div class="clip-main">
                        <div class="clip-play-btn">▶</div>
                        <div class="clip-details">
                            <div class="clip-title">${song.title}</div>
                            <div class="clip-meta">
                                <span class="artist">${song.artist || ''}</span>
                                <span class="tags">${(song.tags || []).join(', ')}</span>
                            </div>
                        </div>
                    </div>
                `;
                div.querySelector('.clip-play-btn').addEventListener('click', () => {
                    // Find a clip for this song to play
                    fetch(`/api/songs/${song.id}/clips`)
                        .then(res => res.json())
                        .then(clips => {
                            if (clips.length > 0) {
                                // We need to attach the song object to the clip for the player
                                clips[0].song = song;
                                playClip(clips[0]);
                            }
                        });
                });
                content.appendChild(div);
            });
            groupDiv.appendChild(header);
            groupDiv.appendChild(content);
            namedSongList.appendChild(groupDiv);
        });
    }

    function handleEdit(e, id, field, clip) {
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
            newEl.addEventListener('click', (e) => handleEdit(e, id, field, clip));
            input.replaceWith(newEl);

            try {
                const body = {};
                body[field] = newVal;
                const endpoint = field === 'title' ? `/api/songs/${clip.song?.id}` : `/api/clips/${id}`;
                if (field === 'title' && !clip.song) return;

                await fetch(endpoint, {
                    method: 'PATCH',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(body)
                });
                
                if (field === 'title' && clip.song) {
                    clip.song.title = newVal;
                    clip.song.is_named = true;
                } else if (field === 'comment') {
                    clip.comment = newVal;
                }
            } catch (err) {
                console.error("Save failed", err);
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
        } catch (err) {
            console.error(err);
        }
    }

    function playClip(clip) {
        currentClip = clip;
        loopMode = 'off';
        loopSection = null;
        activeLoopSegments.clear();
        
        // Minimize markers by default on new song
        markerListContainer.classList.add('collapsed');

        npTitle.textContent = clip.song?.title || `Clip ${clip.id}`;
        npArtist.textContent = `${formatDuration(clip.duration_seconds)} • ${clip.tempo ? Math.round(clip.tempo) + ' BPM' : ''}`;
        
        // Render Tags
        npTags.innerHTML = '';
        (clip.song?.tags || []).forEach(tag => {
            const span = document.createElement('span');
            span.className = 'tag';
            span.textContent = tag;
            npTags.appendChild(span);
        });

        player.src = `/api/clips/${clip.id}/stream`;
        player.load();
        
        player.onloadedmetadata = () => {
            totalTimeSpan.textContent = formatDuration(player.duration);
            to.update({ position: 0, velocity: 1 });
            renderMarkers();
            renderLoopControls();
        };
    }

    function renderMarkers() {
        markerList.innerHTML = '';
        markerTrack.innerHTML = '';
        const markers = [...(currentClip.song?.markers || [])].sort((a, b) => a.start - b.start);
        const duration = player.duration || 0;

        // Auto-collapse if no markers
        if (markers.length === 0) {
            markerListContainer.classList.add('collapsed');
        }

        markers.forEach((m, idx) => {
            // List Item
            const div = document.createElement('div');
            div.className = 'marker-item';
            div.innerHTML = `
                <span class="marker-label">${m.value}</span>
                <span class="marker-time">${formatDuration(m.start)}</span>
                <span class="marker-delete" data-idx="${idx}">×</span>
            `;
            div.addEventListener('click', (e) => {
                if (e.target.className === 'marker-delete') return;
                to.update({ position: m.start, velocity: 1 });
            });
            div.querySelector('.marker-delete').addEventListener('click', async (e) => {
                e.stopPropagation();
                const newMarkers = markers.filter((_, i) => i !== idx);
                try {
                    const res = await fetch(`/api/songs/${currentClip.song.id}`, {
                        method: 'PATCH',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ markers: newMarkers })
                    });
                    currentClip.song = await res.json();
                    renderMarkers();
                } catch (err) { console.error(err); }
            });
            markerList.appendChild(div);

            // Tick on progress bar
            if (duration > 0) {
                const tick = document.createElement('div');
                tick.className = 'marker-tick';
                tick.style.left = `${(m.start / duration) * 100}%`;
                tick.title = m.value;
                markerTrack.appendChild(tick);

                const timelineLabel = document.createElement('div');
                timelineLabel.className = 'marker-label-timeline';
                timelineLabel.style.left = `${(m.start / duration) * 100}%`;
                timelineLabel.textContent = m.value;
                markerTrack.appendChild(timelineLabel);
            }
        });
        
        renderLoopControls();
    }

    // Initial load
    fetchClips();
});
