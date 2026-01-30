import fs from 'node:fs'
import path from 'node:path'

/**
 * Writes dist/CNAME for GitHub Pages custom domains.
 *
 * Default domain: tangyunxuan.com
 * Override with: CNAME_DOMAIN=your.domain npm run build:ghp
 */
const domain = (process.env.CNAME_DOMAIN || 'tangyunxuan.com').trim()

if (!domain) {
  console.error('CNAME_DOMAIN is empty.')
  process.exit(1)
}

const distDir = path.resolve(process.cwd(), 'dist')
fs.mkdirSync(distDir, { recursive: true })
fs.writeFileSync(path.join(distDir, 'CNAME'), `${domain}\n`, 'utf8')

console.log(`Wrote dist/CNAME -> ${domain}`)

