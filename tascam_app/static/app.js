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
    const navRepertoire = document.getElementById('nav-repertoire');
    const navSongs = document.getElementById('nav-songs');
    const navLibrary = document.getElementById('nav-library');
    const repertoireView = document.getElementById('repertoire-view');
    const songsView = document.getElementById('songs-view');
    const libraryView = document.getElementById('library-view');

    // Repertoire Elements
    const repertoireListSection = document.getElementById('repertoire-list-section');
    const repertoireDetailSection = document.getElementById('repertoire-detail-section');
    const repertoireList = document.getElementById('repertoire-list');
    const repertoireItemsList = document.getElementById('repertoire-items-list');
    const btnNewRepertoire = document.getElementById('btn-new-repertoire');
    const btnBackToRepertoires = document.getElementById('btn-back-to-repertoires');
    const repDetailTitle = document.getElementById('rep-detail-title');
    const repDetailDesc = document.getElementById('rep-detail-desc');
    const repDetailMeta = document.getElementById('rep-detail-meta');
    const btnRepPlayAll = document.getElementById('btn-rep-play-all');
    const btnRepAddSongs = document.getElementById('btn-rep-add-songs');
    const btnRepDelete = document.getElementById('btn-rep-delete');
    const btnBatchAddRepertoire = document.getElementById('btn-batch-add-repertoire');
    const batchRepCount = document.getElementById('batch-rep-count');

    // Modals
    const modalNewRep = document.getElementById('modal-new-repertoire');
    const btnCloseNewRepModal = document.getElementById('btn-close-new-rep-modal');
    const btnCancelNewRep = document.getElementById('btn-cancel-new-rep');
    const btnCreateRepSubmit = document.getElementById('btn-create-rep-submit');
    const inputRepName = document.getElementById('input-rep-name');
    const inputRepDesc = document.getElementById('input-rep-desc');
    const inputRepPrivate = document.getElementById('input-rep-private');

    const modalAddToRep = document.getElementById('modal-add-to-repertoire');
    const btnCloseAddToRepModal = document.getElementById('btn-close-add-to-rep-modal');
    const btnCancelAddToRep = document.getElementById('btn-cancel-add-to-rep');
    const addToRepTitle = document.getElementById('add-to-rep-title');
    const addToRepSubtitle = document.getElementById('add-to-rep-subtitle');
    const addToRepOptions = document.getElementById('add-to-rep-options');
    const btnModalOpenCreateRep = document.getElementById('btn-modal-open-create-rep');

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
    const btnInstall = document.getElementById('btn-install');

    // State
    let clips = [];
    let namedSongs = [];
    let repertoires = [];
    let currentRepertoire = null;
    let repertoirePlayback = null; // { repId, items, currentIndex }
    let isAdvancingTrack = false;
    let pendingClipsToAdd = [];
    let currentClip = null;
    let selectedClipIds = new Set();
    let loopMode = 'off';
    let loopSection = null;

    function escapeHTML(str) {
        if (!str) return '';
        return String(str).replace(/[&<>'"]/g, 
            tag => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;' }[tag] || tag)
        );
    }
    // Handle unauthorized calls by clearing all caches and redirecting to root
    async function handleUnauthorized() {
        if ('caches' in window) {
            try {
                const keys = await caches.keys();
                await Promise.all(keys.map(key => caches.delete(key)));
            } catch (err) {
                console.error('Failed to clear cache on 401:', err);
            }
        }
        window.location.href = '/';
    }

    // Toggle Markers
    const markerHeader = document.querySelector('.marker-header');
    if (markerHeader) {
        markerHeader.addEventListener('click', () => {
            markerListContainer.classList.toggle('collapsed');
        });
    }

    // PWA Install Logic
    let deferredPrompt;
    window.addEventListener('beforeinstallprompt', (e) => {
        // Prevent the mini-infobar from appearing on mobile
        e.preventDefault();
        // Stash the event so it can be triggered later.
        deferredPrompt = e;
        // Update UI notify the user they can install the PWA
        if (btnInstall) {
            btnInstall.classList.remove('hidden');
        }
    });

    if (btnInstall) {
        btnInstall.addEventListener('click', async () => {
            if (deferredPrompt) {
                deferredPrompt.prompt();
                const { outcome } = await deferredPrompt.userChoice;
                console.log(`User response to the install prompt: ${outcome}`);
                deferredPrompt = null;
                btnInstall.classList.add('hidden');
            }
        });
    }

    window.addEventListener('appinstalled', () => {
        console.log('PWA was installed');
        if (btnInstall) btnInstall.classList.add('hidden');
    });

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
        } else if (loopMode === 'off' && repertoirePlayback && duration > 0 && pos >= duration - 0.15) {
            playNextRepertoireTrack();
        }
    });

    // Fallback for when the audio element completely ends
    player.addEventListener('ended', () => {
        if (loopMode !== 'off' && loopSection) {
            to.update({ position: loopSection.start, velocity: 1 });
        } else if (loopMode === 'off' && repertoirePlayback) {
            playNextRepertoireTrack();
        }
    });

    to.on("change", () => {
        const vector = to.query();
        btnPlayPause.textContent = vector.velocity === 0 ? "Play" : "Pause";
    });

    // Navigation Buttons
    navRepertoire.addEventListener('click', () => {
        navRepertoire.classList.add('active');
        navSongs.classList.remove('active');
        navLibrary.classList.remove('active');
        repertoireView.classList.remove('hidden');
        songsView.classList.add('hidden');
        libraryView.classList.add('hidden');
        fetchRepertoires();
    });

    navLibrary.addEventListener('click', () => {
        navLibrary.classList.add('active');
        navRepertoire.classList.remove('active');
        navSongs.classList.remove('active');
        libraryView.classList.remove('hidden');
        repertoireView.classList.add('hidden');
        songsView.classList.add('hidden');
    });

    navSongs.addEventListener('click', () => {
        navSongs.classList.add('active');
        navRepertoire.classList.remove('active');
        navLibrary.classList.remove('active');
        songsView.classList.remove('hidden');
        repertoireView.classList.add('hidden');
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
            if (res.status === 401) {
                handleUnauthorized();
                return;
            }
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
            .then(res => {
                if (res.status === 401) {
                    handleUnauthorized();
                    throw new Error('Unauthorized');
                }
                return res.json();
            })
            .then(data => {
                clips = data;
                renderGroups(songList, clips);
            })
            .catch(err => {
                if (err.message !== 'Unauthorized') {
                    songList.innerHTML = '<div class="error">Failed to load library</div>';
                    console.error(err);
                }
            });
    }

    function fetchNamedSongs() {
        fetch('/api/songs/named')
            .then(res => {
                if (res.status === 401) {
                    handleUnauthorized();
                    throw new Error('Unauthorized');
                }
                return res.json();
            })
            .then(data => {
                namedSongs = data;
                renderNamedSongs();
            })
            .catch(err => {
                if (err.message !== 'Unauthorized') {
                    namedSongList.innerHTML = '<div class="error">Failed to load songs</div>';
                    console.error(err);
                }
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
        if (batchRepCount) batchRepCount.textContent = count;
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

        let privateToggleHTML = '';
        if (window.IS_ADMIN) {
            privateToggleHTML = `
                <div class="private-toggle-container" title="Private (Admin only)">
                    <span>🔒</span>
                    <label class="switch">
                        <input type="checkbox" class="clip-private-toggle" ${clip.is_private ? 'checked' : ''}>
                        <span class="slider"></span>
                    </label>
                </div>
            `;
        }

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
                <button class="btn-add-rep" title="Legg til i repertoar">+ Rep</button>
                ${privateToggleHTML}
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

        div.querySelector('.btn-add-rep').addEventListener('click', (e) => {
            e.stopPropagation();
            openAddToRepertoireModal([clip.id], songTitle);
        });

        if (window.IS_ADMIN) {
            const privateToggle = div.querySelector('.clip-private-toggle');
            if (privateToggle) {
                privateToggle.addEventListener('change', async (e) => {
                    const isPrivate = e.target.checked;
                    try {
                        const res = await fetch(`/api/clips/${clip.id}`, {
                            method: 'PATCH',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ is_private: isPrivate })
                        });
                        if (res.status === 401) {
                            handleUnauthorized();
                            return;
                        }
                        if (!res.ok) throw new Error("Failed to update");
                        clip.is_private = isPrivate;
                    } catch (err) {
                        console.error(err);
                        e.target.checked = !isPrivate;
                        alert("Failed to update privacy");
                    }
                });
            }
        }

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
                let privateToggleHTML = '';
                if (window.IS_ADMIN) {
                    privateToggleHTML = `
                        <div class="private-toggle-container" title="Private (Admin only)">
                            <span>🔒</span>
                            <label class="switch">
                                <input type="checkbox" class="song-private-toggle" ${song.is_private ? 'checked' : ''}>
                                <span class="slider"></span>
                            </label>
                        </div>
                    `;
                }

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
                    <div class="clip-actions">
                        <button class="btn-add-rep" title="Legg til i repertoar">+ Rep</button>
                        ${privateToggleHTML}
                    </div>
                `;

                div.querySelector('.btn-add-rep').addEventListener('click', async (e) => {
                    e.stopPropagation();
                    try {
                        const res = await fetch(`/api/songs/${song.id}/clips`);
                        if (res.status === 401) {
                            handleUnauthorized();
                            return;
                        }
                        const songClips = await res.json();
                        if (songClips && songClips.length > 0) {
                            openAddToRepertoireModal([songClips[0].id], song.title);
                        } else {
                            alert("Ingen opptak funnet for denne sangen.");
                        }
                    } catch (err) {
                        console.error(err);
                    }
                });

                if (window.IS_ADMIN) {
                    const privateToggle = div.querySelector('.song-private-toggle');
                    if (privateToggle) {
                        privateToggle.addEventListener('change', async (e) => {
                            const isPrivate = e.target.checked;
                            try {
                                const res = await fetch(`/api/songs/${song.id}`, {
                                    method: 'PATCH',
                                    headers: { 'Content-Type': 'application/json' },
                                    body: JSON.stringify({ is_private: isPrivate })
                                });
                                if (res.status === 401) {
                                    handleUnauthorized();
                                    return;
                                }
                                if (!res.ok) throw new Error("Failed to update");
                                song.is_private = isPrivate;
                            } catch (err) {
                                console.error(err);
                                e.target.checked = !isPrivate;
                                alert("Failed to update privacy");
                            }
                        });
                    }
                }

                div.querySelector('.clip-play-btn').addEventListener('click', () => {
                    // Find a clip for this song to play
                    fetch(`/api/songs/${song.id}/clips`)
                        .then(res => {
                            if (res.status === 401) {
                                handleUnauthorized();
                                throw new Error('Unauthorized');
                            }
                            return res.json();
                        })
                        .then(clips => {
                            if (clips.length > 0) {
                                // We need to attach the song object to the clip for the player
                                clips[0].song = song;
                                playClip(clips[0]);
                            }
                        })
                        .catch(err => {
                            if (err.message !== 'Unauthorized') {
                                console.error(err);
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

                const res = await fetch(endpoint, {
                    method: 'PATCH',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(body)
                });
                if (res.status === 401) {
                    handleUnauthorized();
                    return;
                }
                
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
            const res = await fetch(`/api/clips/${id}`, { method: 'DELETE' });
            if (res.status === 401) {
                handleUnauthorized();
                return;
            }
            el.remove();
        } catch (err) {
            console.error(err);
        }
    }

    function playClip(clip, isRepertoirePlay = false) {
        if (!isRepertoirePlay) {
            repertoirePlayback = null;
            highlightActiveRepertoireItem(-1);
        }
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

            // Drag-to-Nudge Logic
            let startX = 0;
            let startT = m.start;
            let currentT = m.start;
            let isDragging = false;
            const threshold = 5; // pixels before we consider it a drag
            const sensitivity = 0.01; // seconds per pixel

            div.addEventListener('pointerdown', (e) => {
                if (e.target.className === 'marker-delete') return;
                div.setPointerCapture(e.pointerId);
                startX = e.clientX;
                startT = m.start;
                isDragging = false;
            });

            div.addEventListener('pointermove', (e) => {
                if (!div.hasPointerCapture(e.pointerId)) return;
                
                const deltaX = e.clientX - startX;
                
                if (!isDragging && Math.abs(deltaX) > threshold) {
                    isDragging = true;
                    div.classList.add('is-nudging');
                }

                if (isDragging) {
                    // Update current time locally
                    currentT = Math.max(0, Math.min(player.duration || 9999, startT + (deltaX * sensitivity)));
                    div.querySelector('.marker-time').textContent = formatDuration(currentT);
                }
            });

            div.addEventListener('pointerup', async (e) => {
                if (!div.hasPointerCapture(e.pointerId)) return;
                div.releasePointerCapture(e.pointerId);
                
                if (!isDragging) {
                    // It was a tap, just jump and play
                    to.update({ position: m.start, velocity: 1 });
                } else {
                    // It was a drag, save the new time
                    div.classList.remove('is-nudging');
                    
                    const updatedMarkers = [...currentClip.song.markers];
                    updatedMarkers[idx] = { ...updatedMarkers[idx], start: currentT };
                    
                    try {
                        const res = await fetch(`/api/songs/${currentClip.song.id}`, {
                            method: 'PATCH',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ markers: updatedMarkers })
                        });
                        if (res.status === 401) {
                            handleUnauthorized();
                            return;
                        }
                        currentClip.song = await res.json();
                        renderMarkers();
                        
                        // Auto-play from the new spot as requested
                        to.update({ position: currentT, velocity: 1 });
                    } catch (err) {
                        console.error(err);
                        renderMarkers(); // Revert UI
                    }
                }
                isDragging = false;
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
                    if (res.status === 401) {
                        handleUnauthorized();
                        return;
                    }
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

    // ==========================================
    // Continuous Setlist Playback
    // ==========================================
    function highlightActiveRepertoireItem(activeIdx) {
        if (!repertoireItemsList) return;
        const rows = repertoireItemsList.querySelectorAll('.repertoire-item-row');
        rows.forEach((row, idx) => {
            row.classList.toggle('is-active', idx === activeIdx);
        });
    }

    function playNextRepertoireTrack() {
        if (!repertoirePlayback || isAdvancingTrack) return;
        isAdvancingTrack = true;
        setTimeout(() => { isAdvancingTrack = false; }, 800);

        const { items, currentIndex } = repertoirePlayback;
        if (currentIndex + 1 < items.length) {
            repertoirePlayback.currentIndex = currentIndex + 1;
            const nextItem = items[repertoirePlayback.currentIndex];
            if (nextItem && nextItem.clip) {
                if (!nextItem.clip.song && nextItem.song) {
                    nextItem.clip.song = nextItem.song;
                }
                highlightActiveRepertoireItem(repertoirePlayback.currentIndex);
                playClip(nextItem.clip, true);
            }
        } else {
            // Reached the end of the setlist
            repertoirePlayback = null;
            highlightActiveRepertoireItem(-1);
        }
    }

    // ==========================================
    // Repertoire Management Logic
    // ==========================================
    async function fetchRepertoires() {
        if (!repertoireList) return;
        try {
            const res = await fetch('/api/repertoires');
            if (res.status === 401) {
                handleUnauthorized();
                return;
            }
            if (!res.ok) throw new Error("Failed to load repertoires");
            repertoires = await res.json();
            renderRepertoireList();
        } catch (err) {
            console.error(err);
            repertoireList.innerHTML = '<div class="error">Kunne ikke laste repertoarer</div>';
        }
    }

    function renderRepertoireList() {
        if (!repertoireList) return;
        repertoireList.innerHTML = '';
        if (!repertoires || repertoires.length === 0) {
            repertoireList.innerHTML = `
                <div class="empty-state" style="grid-column: 1 / -1; padding: 40px 20px; text-align: center; color: var(--text-secondary); background: var(--bg-card); border: 1px solid var(--border); border-radius: 8px;">
                    <p style="font-size: 1.1rem; margin-bottom: 10px;">Ingen repertoarer opprettet enda.</p>
                    <p style="font-size: 0.9rem;">Klikk på <strong>+ Nytt repertoar</strong> for å lage din første settliste!</p>
                </div>
            `;
            return;
        }

        repertoires.forEach(rep => {
            const card = document.createElement('div');
            card.className = 'repertoire-card';
            card.innerHTML = `
                <div>
                    <div class="repertoire-card-header">
                        <h3 class="repertoire-card-title">${escapeHTML(rep.name)}</h3>
                        ${rep.is_private ? '<span title="Privat">🔒</span>' : ''}
                    </div>
                    <div class="repertoire-card-desc">${rep.description ? escapeHTML(rep.description) : '<span style="font-style: italic;">Ingen beskrivelse</span>'}</div>
                </div>
                <div class="repertoire-card-footer">
                    <div class="repertoire-card-stats">
                        <span>🎵 ${rep.item_count} ${rep.item_count === 1 ? 'låt' : 'låter'}</span>
                        <span>⏱ ${formatDuration(rep.total_duration_seconds)}</span>
                    </div>
                    <span style="color: var(--accent); font-weight: 500;">Åpne →</span>
                </div>
            `;
            card.addEventListener('click', () => openRepertoire(rep.id));
            repertoireList.appendChild(card);
        });
    }

    async function openRepertoire(repId) {
        try {
            const res = await fetch(`/api/repertoires/${repId}`);
            if (res.status === 401) {
                handleUnauthorized();
                return;
            }
            if (!res.ok) throw new Error("Failed to load repertoire");
            currentRepertoire = await res.json();
            if (repertoireListSection) repertoireListSection.classList.add('hidden');
            if (repertoireDetailSection) repertoireDetailSection.classList.remove('hidden');
            renderRepertoireDetail();
        } catch (err) {
            console.error(err);
            alert("Kunne ikke åpne repertoaret");
        }
    }

    function renderRepertoireDetail() {
        if (!currentRepertoire) return;

        if (repDetailTitle) repDetailTitle.textContent = currentRepertoire.name;
        if (repDetailDesc) repDetailDesc.textContent = currentRepertoire.description || 'Legg til beskrivelse...';
        if (repDetailMeta) {
            repDetailMeta.innerHTML = `
                <span>🎵 ${currentRepertoire.item_count} ${currentRepertoire.item_count === 1 ? 'låt' : 'låter'}</span>
                <span>⏱ ${formatDuration(currentRepertoire.total_duration_seconds)} samlet spilletid</span>
                ${currentRepertoire.is_private ? '<span>🔒 Privat</span>' : ''}
            `;
        }

        if (!repertoireItemsList) return;
        repertoireItemsList.innerHTML = '';
        const items = currentRepertoire.items || [];

        if (items.length === 0) {
            repertoireItemsList.innerHTML = `
                <div style="padding: 30px 20px; text-align: center; color: var(--text-secondary); background: var(--bg-card); border: 1px solid var(--border); border-radius: 8px;">
                    <p style="margin-bottom: 10px;">Dette repertoaret er tomt.</p>
                    <p style="font-size: 0.9rem;">Gå til <strong>Library</strong> eller <strong>Songs</strong> og klikk <strong>+ Rep</strong> for å legge til låter.</p>
                </div>
            `;
            return;
        }

        items.forEach((item, idx) => {
            const clip = item.clip;
            const songTitle = (clip && clip.song?.title) ? clip.song.title : (item.song?.title || `Opptak #${item.clip_id || item.id}`);
            const durationStr = clip ? formatDuration(clip.duration_seconds) : '-';
            const tempoStr = (clip && clip.tempo) ? `${Math.round(clip.tempo)} BPM` : '';
            const notesStr = item.notes || '';

            const row = document.createElement('div');
            row.className = 'repertoire-item-row';
            row.dataset.itemId = item.id;
            row.dataset.idx = idx;

            if (repertoirePlayback && repertoirePlayback.repId === currentRepertoire.id && repertoirePlayback.currentIndex === idx) {
                row.classList.add('is-active');
            }

            row.innerHTML = `
                <div class="rep-item-left">
                    <div class="rep-item-reorder">
                        <button class="btn-reorder btn-move-up" title="Flytt opp" ${idx === 0 ? 'disabled' : ''}>▲</button>
                        <button class="btn-reorder btn-move-down" title="Flytt ned" ${idx === items.length - 1 ? 'disabled' : ''}>▼</button>
                    </div>
                    <span class="rep-item-pos">#${idx + 1}</span>
                    <div class="clip-play-btn" title="Spill fra denne låten">▶</div>
                    <div class="rep-item-details">
                        <div class="rep-item-title">${escapeHTML(songTitle)}</div>
                        <div class="rep-item-meta">
                            <span>${durationStr}</span>
                            ${tempoStr ? `<span>${tempoStr}</span>` : ''}
                            <span class="rep-item-notes" data-empty="${notesStr ? 'false' : 'true'}" title="Klikk for å endre notat">${notesStr ? escapeHTML(notesStr) : ''}</span>
                        </div>
                    </div>
                </div>
                <div class="clip-actions">
                    <button class="btn-delete btn-remove-item" title="Fjern fra repertoar">✕</button>
                </div>
            `;

            // Play from here
            row.querySelector('.clip-play-btn').addEventListener('click', (e) => {
                e.stopPropagation();
                if (clip) {
                    if (!clip.song && item.song) {
                        clip.song = item.song;
                    }
                    repertoirePlayback = {
                        repId: currentRepertoire.id,
                        items: currentRepertoire.items,
                        currentIndex: idx
                    };
                    highlightActiveRepertoireItem(idx);
                    playClip(clip, true);
                }
            });

            // Move Up
            row.querySelector('.btn-move-up').addEventListener('click', (e) => {
                e.stopPropagation();
                if (idx > 0) moveRepertoireItem(idx, idx - 1);
            });

            // Move Down
            row.querySelector('.btn-move-down').addEventListener('click', (e) => {
                e.stopPropagation();
                if (idx < items.length - 1) moveRepertoireItem(idx, idx + 1);
            });

            // Edit Notes
            const notesEl = row.querySelector('.rep-item-notes');
            notesEl.addEventListener('click', (e) => {
                e.stopPropagation();
                handleEditItemNotes(item, notesEl);
            });

            // Remove from Repertoire
            row.querySelector('.btn-remove-item').addEventListener('click', async (e) => {
                e.stopPropagation();
                if (confirm(`Fjern "${songTitle}" fra dette repertoaret?`)) {
                    await deleteRepertoireItem(item.id);
                }
            });

            repertoireItemsList.appendChild(row);
        });
    }

    async function moveRepertoireItem(fromIdx, toIdx) {
        if (!currentRepertoire || !currentRepertoire.items) return;
        const items = [...currentRepertoire.items];
        const [moved] = items.splice(fromIdx, 1);
        items.splice(toIdx, 0, moved);

        items.forEach((item, idx) => item.position = idx);
        currentRepertoire.items = items;
        renderRepertoireDetail();

        try {
            const itemIds = items.map(i => i.id);
            const res = await fetch(`/api/repertoires/${currentRepertoire.id}/reorder`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ item_ids: itemIds })
            });
            if (res.status === 401) {
                handleUnauthorized();
                return;
            }
            if (!res.ok) throw new Error("Failed to reorder");
        } catch (err) {
            console.error(err);
            alert("Kunne ikke lagre ny rekkefølge");
            openRepertoire(currentRepertoire.id);
        }
    }

    function handleEditItemNotes(item, notesEl) {
        const currentNotes = item.notes || '';
        const input = document.createElement('input');
        input.type = 'text';
        input.value = currentNotes;
        input.className = 'edit-input';
        input.placeholder = 'F.eks. Drop D, 4 takter intro...';
        notesEl.replaceWith(input);
        input.focus();

        const save = async () => {
            const newNotes = input.value.trim();
            item.notes = newNotes;
            renderRepertoireDetail();

            try {
                const res = await fetch(`/api/repertoires/${currentRepertoire.id}/items/${item.id}`, {
                    method: 'PATCH',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ notes: newNotes })
                });
                if (res.status === 401) {
                    handleUnauthorized();
                    return;
                }
                if (!res.ok) throw new Error("Failed to update notes");
            } catch (err) {
                console.error(err);
            }
        };

        input.addEventListener('blur', save);
        input.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') save();
        });
    }

    async function deleteRepertoireItem(itemId) {
        try {
            const res = await fetch(`/api/repertoires/${currentRepertoire.id}/items/${itemId}`, {
                method: 'DELETE'
            });
            if (res.status === 401) {
                handleUnauthorized();
                return;
            }
            if (!res.ok) throw new Error("Failed to delete item");
            await openRepertoire(currentRepertoire.id);
        } catch (err) {
            console.error(err);
            alert("Kunne ikke fjerne låten");
        }
    }

    async function updateRepertoireMeta(fields) {
        try {
            const res = await fetch(`/api/repertoires/${currentRepertoire.id}`, {
                method: 'PATCH',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(fields)
            });
            if (res.status === 401) {
                handleUnauthorized();
                return;
            }
            if (!res.ok) throw new Error("Failed to update repertoire");
            const updated = await res.json();
            currentRepertoire.name = updated.name;
            currentRepertoire.description = updated.description;
            renderRepertoireDetail();
        } catch (err) {
            console.error(err);
            alert("Kunne ikke oppdatere repertoar");
        }
    }

    if (repDetailTitle) {
        repDetailTitle.addEventListener('click', () => {
            if (!currentRepertoire) return;
            const newName = prompt("Endre navn på repertoar:", currentRepertoire.name);
            if (newName && newName.trim() && newName.trim() !== currentRepertoire.name) {
                updateRepertoireMeta({ name: newName.trim() });
            }
        });
    }

    if (repDetailDesc) {
        repDetailDesc.addEventListener('click', () => {
            if (!currentRepertoire) return;
            const newDesc = prompt("Endre beskrivelse:", currentRepertoire.description || "");
            if (newDesc !== null && newDesc.trim() !== (currentRepertoire.description || "")) {
                updateRepertoireMeta({ description: newDesc.trim() });
            }
        });
    }

    if (btnBackToRepertoires) {
        btnBackToRepertoires.addEventListener('click', () => {
            if (repertoireDetailSection) repertoireDetailSection.classList.add('hidden');
            if (repertoireListSection) repertoireListSection.classList.remove('hidden');
            currentRepertoire = null;
            fetchRepertoires();
        });
    }

    if (btnRepPlayAll) {
        btnRepPlayAll.addEventListener('click', () => {
            if (!currentRepertoire || !currentRepertoire.items || currentRepertoire.items.length === 0) {
                alert("Ingen sanger i dette repertoaret.");
                return;
            }
            const firstItem = currentRepertoire.items[0];
            if (firstItem && firstItem.clip) {
                if (!firstItem.clip.song && firstItem.song) {
                    firstItem.clip.song = firstItem.song;
                }
                repertoirePlayback = {
                    repId: currentRepertoire.id,
                    items: currentRepertoire.items,
                    currentIndex: 0
                };
                highlightActiveRepertoireItem(0);
                playClip(firstItem.clip, true);
            }
        });
    }

    if (btnRepAddSongs) {
        btnRepAddSongs.addEventListener('click', () => {
            navLibrary.click();
        });
    }

    if (btnRepDelete) {
        btnRepDelete.addEventListener('click', async () => {
            if (!currentRepertoire) return;
            if (confirm(`Er du sikker på at du vil slette repertoaret "${currentRepertoire.name}"? Lydfilene og sangene blir værende i biblioteket.`)) {
                try {
                    const res = await fetch(`/api/repertoires/${currentRepertoire.id}`, {
                        method: 'DELETE'
                    });
                    if (res.status === 401) {
                        handleUnauthorized();
                        return;
                    }
                    if (!res.ok) throw new Error("Failed to delete repertoire");
                    if (repertoireDetailSection) repertoireDetailSection.classList.add('hidden');
                    if (repertoireListSection) repertoireListSection.classList.remove('hidden');
                    currentRepertoire = null;
                    fetchRepertoires();
                } catch (err) {
                    console.error(err);
                    alert("Kunne ikke slette repertoaret");
                }
            }
        });
    }

    // ==========================================
    // Modals: Add to Repertoire & Create New
    // ==========================================
    function openNewRepertoireModal(clipIds = null) {
        if (clipIds) pendingClipsToAdd = clipIds;
        if (modalNewRep) modalNewRep.classList.remove('hidden');
        if (inputRepName) {
            inputRepName.value = '';
            inputRepName.focus();
        }
        if (inputRepDesc) inputRepDesc.value = '';
        if (inputRepPrivate) inputRepPrivate.checked = false;
    }

    function closeNewRepertoireModal() {
        if (modalNewRep) modalNewRep.classList.add('hidden');
    }

    if (btnNewRepertoire) {
        btnNewRepertoire.addEventListener('click', () => openNewRepertoireModal());
    }
    if (btnCloseNewRepModal) btnCloseNewRepModal.addEventListener('click', closeNewRepertoireModal);
    if (btnCancelNewRep) btnCancelNewRep.addEventListener('click', closeNewRepertoireModal);

    if (btnCreateRepSubmit) {
        btnCreateRepSubmit.addEventListener('click', async () => {
            const name = inputRepName.value.trim();
            if (!name) {
                alert("Vennligst skriv inn et navn på repertoaret.");
                inputRepName.focus();
                return;
            }
            const description = inputRepDesc.value.trim();
            const is_private = inputRepPrivate ? inputRepPrivate.checked : false;

            try {
                const res = await fetch('/api/repertoires', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ name, description, is_private })
                });
                if (res.status === 401) {
                    handleUnauthorized();
                    return;
                }
                if (!res.ok) throw new Error("Failed to create repertoire");
                const newRep = await res.json();
                closeNewRepertoireModal();

                if (pendingClipsToAdd && pendingClipsToAdd.length > 0) {
                    await addPendingClipsToRepertoire(newRep.id, newRep.name);
                }

                navRepertoire.click();
                openRepertoire(newRep.id);
            } catch (err) {
                console.error(err);
                alert("Kunne ikke opprette repertoar");
            }
        });
    }

    async function openAddToRepertoireModal(clipIds, displayName) {
        pendingClipsToAdd = clipIds;
        if (modalAddToRep) modalAddToRep.classList.remove('hidden');
        if (addToRepSubtitle) addToRepSubtitle.textContent = displayName || `${clipIds.length} valgte opptak`;
        if (addToRepOptions) addToRepOptions.innerHTML = '<div class="loading">Laster repertoarer...</div>';

        try {
            const res = await fetch('/api/repertoires');
            if (res.status === 401) {
                handleUnauthorized();
                return;
            }
            const repList = await res.json();
            renderAddToRepOptions(repList);
        } catch (err) {
            console.error(err);
            if (addToRepOptions) addToRepOptions.innerHTML = '<div class="error">Kunne ikke hente repertoarer</div>';
        }
    }

    function renderAddToRepOptions(repList) {
        if (!addToRepOptions) return;
        addToRepOptions.innerHTML = '';
        if (!repList || repList.length === 0) {
            addToRepOptions.innerHTML = '<p class="text-secondary" style="font-size: 0.9rem; text-align: center; padding: 10px;">Ingen repertoarer funnet. Opprett et nytt nedenfor!</p>';
            return;
        }

        repList.forEach(rep => {
            const item = document.createElement('div');
            item.className = 'rep-select-item';
            item.innerHTML = `
                <span class="rep-select-name">${escapeHTML(rep.name)}</span>
                <span class="rep-select-count">${rep.item_count} ${rep.item_count === 1 ? 'låt' : 'låter'}</span>
            `;
            item.addEventListener('click', async () => {
                await addPendingClipsToRepertoire(rep.id, rep.name);
            });
            addToRepOptions.appendChild(item);
        });
    }

    async function addPendingClipsToRepertoire(repId, repName) {
        if (!pendingClipsToAdd || pendingClipsToAdd.length === 0) return;
        try {
            const res = await fetch(`/api/repertoires/${repId}/items/batch`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ clip_ids: pendingClipsToAdd })
            });
            if (res.status === 401) {
                handleUnauthorized();
                return;
            }
            if (!res.ok) throw new Error("Failed to add clips to repertoire");
            const data = await res.json();

            if (modalAddToRep) modalAddToRep.classList.add('hidden');
            alert(`${data.added_count} låt(er) lagt til i "${repName}"!`);

            // Clear selection in recordings
            selectedClipIds.clear();
            document.querySelectorAll('.clip-checkbox:checked').forEach(cb => cb.checked = false);
            updateBatchActions();
            pendingClipsToAdd = [];
        } catch (err) {
            console.error(err);
            alert("Kunne ikke legge til i repertoaret");
        }
    }

    if (btnModalOpenCreateRep) {
        btnModalOpenCreateRep.addEventListener('click', () => {
            if (modalAddToRep) modalAddToRep.classList.add('hidden');
            openNewRepertoireModal(pendingClipsToAdd);
        });
    }

    if (btnCloseAddToRepModal) {
        btnCloseAddToRepModal.addEventListener('click', () => {
            if (modalAddToRep) modalAddToRep.classList.add('hidden');
            pendingClipsToAdd = [];
        });
    }

    if (btnCancelAddToRep) {
        btnCancelAddToRep.addEventListener('click', () => {
            if (modalAddToRep) modalAddToRep.classList.add('hidden');
            pendingClipsToAdd = [];
        });
    }

    if (btnBatchAddRepertoire) {
        btnBatchAddRepertoire.addEventListener('click', () => {
            if (selectedClipIds.size === 0) return;
            const ids = Array.from(selectedClipIds);
            openAddToRepertoireModal(ids, `${ids.length} valgte opptak fra Recordings`);
        });
    }

    // Initial load
    fetchRepertoires();
    fetchNamedSongs();
    fetchClips(); // Still fetch clips in background so the library is ready when toggled
});
