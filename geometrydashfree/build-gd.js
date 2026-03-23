const { execSync } = require('child_process');
const fs = require('fs');

async function scrapeAndBuild() {
    const query = "Geometry Dash";
    // Scratch API search endpoint (limit set to 10 for safety; max is 40)
    const url = `https://api.scratch.mit.edu{encodeURIComponent(query)}&limit=10&mode=trending`;

    try {
        console.log(`Searching Scratch for: "${query}"...`);
        const response = await fetch(url);
        const projects = await response.json();

        if (!projects || projects.length === 0) {
            console.log("No projects found.");
            return;
        }

        const outputDir = './games';
        if (!fs.existsSync(outputDir)) fs.mkdirSync(outputDir);

        for (const project of projects) {
            const id = project.id;
            const title = project.title;

            // Only process if "Geometry Dash" is actually in the name
            if (title.toLowerCase().includes("geometry dash")) {
                console.log(`--- Processing: ${title} (ID: ${id}) ---`);
                
                try {
                    // 1. Download .sb3
                    execSync(`npx @turbowarp/sbdl ${id} -o temp.sb3`);
                    
                    // 2. Compile to HTML folder
                    execSync(`npx turbowarp-packager-cli -i temp.sb3 -o ${outputDir}/${id}`);
                    
                    // 3. Clean up
                    fs.unlinkSync('temp.sb3');
                    console.log(`Success: ${id} compiled.`);
                } catch (err) {
                    console.error(`Error compiling ${id}:`, err.message);
                }
            }
        }
    } catch (error) {
        console.error("Failed to scrape Scratch API:", error.message);
    }
}

scrapeAndBuild();
