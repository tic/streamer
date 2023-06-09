const collectionToArray = (collection) => {
  const arr = [];
  for (let i = 0; i < collection.length; i++) {
    arr.push(collection.item(i));
  }
  return arr;
}