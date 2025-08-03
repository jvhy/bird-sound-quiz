/* Implementation of the presentation of the audio player */
const carouselEl = document.querySelector("#quizCarousel");
const activeSlide = carouselEl.querySelector(".carousel-item.active");
const playIconContainer = activeSlide.querySelector('#play-icon');
const audioPlayerContainer = activeSlide.querySelector('#audio-player-container');
const seekSlider = activeSlide.querySelector('#seek-slider');
const volumeSlider = activeSlide.querySelector('#volume-slider');
const muteIconContainer = activeSlide.querySelector('#mute-icon');
let playState = 'play';
let muteState = 'unmute';


playIconContainer.addEventListener('click', () => {
    if(playState === 'play') {
        audio.play();
        playState = 'pause';
    } else {
        audio.pause();
        playState = 'play';
    }
});

muteIconContainer.addEventListener('click', () => {
    if(muteState === 'unmute') {
        audio.muted = true;
        muteState = 'mute';
    } else {
        audio.muted = false;
        muteState = 'unmute';
    }
});

const showRangeProgress = (rangeInput) => {
    if(rangeInput === seekSlider) audioPlayerContainer.style.setProperty('--seek-before-width', rangeInput.value / rangeInput.max * 100 + '%');
    else audioPlayerContainer.style.setProperty('--volume-before-width', rangeInput.value / rangeInput.max * 100 + '%');
}

seekSlider.addEventListener('input', (e) => {
    showRangeProgress(e.target);
});
volumeSlider.addEventListener('input', (e) => {
    showRangeProgress(e.target);
});


/* Implementation of the functionality of the audio player */
const audio = activeSlide.querySelector('audio');
const durationContainer = activeSlide.querySelector('#duration');
const currentTimeContainer = activeSlide.querySelector('#current-time');
const outputContainer = activeSlide.querySelector('#volume-output');
let raf = null;

const calculateTime = (secs) => {
    const minutes = Math.floor(secs / 60);
    const seconds = Math.floor(secs % 60);
    const returnedSeconds = seconds < 10 ? `0${seconds}` : `${seconds}`;
    return `${minutes}:${returnedSeconds}`;
}

const displayDuration = () => {
    durationContainer.textContent = calculateTime(audio.duration);
}

const setSliderMax = () => {
    seekSlider.max = Math.floor(audio.duration);
}

const displayBufferedAmount = () => {
    const bufferedAmount = Math.floor(audio.buffered.end(audio.buffered.length - 1));
    audioPlayerContainer.style.setProperty('--buffered-width', `${(bufferedAmount / seekSlider.max) * 100}%`);
}

const whilePlaying = () => {
    seekSlider.value = Math.floor(audio.currentTime);
    currentTimeContainer.textContent = calculateTime(seekSlider.value);
    audioPlayerContainer.style.setProperty('--seek-before-width', `${seekSlider.value / seekSlider.max * 100}%`);
    raf = requestAnimationFrame(whilePlaying);
}

if (audio.readyState > 0) {
    displayDuration();
    setSliderMax();
    displayBufferedAmount();
} else {
    audio.addEventListener('loadedmetadata', () => {
        displayDuration();
        setSliderMax();
        displayBufferedAmount();
    });
}

audio.addEventListener('progress', displayBufferedAmount);

seekSlider.addEventListener('input', () => {
    currentTimeContainer.textContent = calculateTime(seekSlider.value);
    if(!audio.paused) {
        cancelAnimationFrame(raf);
    }
});

seekSlider.addEventListener('change', () => {
    audio.currentTime = seekSlider.value;
    if(!audio.paused) {
        requestAnimationFrame(whilePlaying);
    }
});

volumeSlider.addEventListener('input', (e) => {
    const value = e.target.value;

    outputContainer.textContent = value;
    audio.volume = value / 100;
});
