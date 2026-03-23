const { execSync } = require('child_process');
const fs = require('fs');

const projectIds = ['105500895', '523661132']; // Your GD IDs

projectIds.forEach(id => {
  console.log(`Building GD Game: ${id}`);
  // Download .sb3
  execSync(`npx @turbowarp/sbdl ${id} -o temp.sb3`);
  // Package to HTML folder
  execSync(`npx turbowarp-packager-cli -i temp.sb3 -o ./dist/${id}`);
  fs.unlinkSync('temp.sb3');
});
