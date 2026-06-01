const fs = require('fs');
const postcss = require('postcss');
const tailwindPostcss = require('@tailwindcss/postcss');
const autoprefixer = require('autoprefixer');

const inputPath = process.argv[2];
if (!inputPath) {
  console.error('Usage: node postcss-debug-run.js <input-css-path>');
  process.exit(1);
}

const css = fs.readFileSync(inputPath, 'utf8');

postcss([
  tailwindPostcss({ config: 'tailwind.config.js' }),
  autoprefixer(),
])
  .process(css, { from: inputPath })
  .then((result) => {
    console.log(result.css.slice(0, 500));
    console.log('\n---');
    console.log('HAS_TAILWIND_OUTPUT=' + result.css.includes('.bg-slate-950'));
  })
  .catch((e) => {
    console.error(e);
    process.exit(1);
  });

