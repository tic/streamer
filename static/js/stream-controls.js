collectionToArray(document.getElementsByClassName('streamControls')).forEach((container) => {
  const pausePlay = container.getElementsByClassName('pausePlay')[0];
  pausePlay.addEventListener('click', function() {
    const nextState = pausePlay.classList.contains('pause') ? 'play' : 'pause';
    pausePlay.classList = `pausePlay ${nextState}`;
    collectionToArray(document.getElementsByTagName('img')).forEach((target) => {
      const src = target.getAttribute('src');
      const camera_id = src.match(/\/.+\/(\d+)/)[1];
      target.setAttribute('src', `/${nextState === 'play' ? 'image' : 'feed'}/${camera_id}?t=${Date.now()}`);
    });
  }, false);
});
