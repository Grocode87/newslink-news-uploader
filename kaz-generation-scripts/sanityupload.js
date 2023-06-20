const sanityClient = require('@sanity/client')
const fs = require('fs')
const path = require('path')
const grayMatter = require('gray-matter')

const client = sanityClient.createClient({
  projectId: 'lolek1cy',
  dataset: 'production',
  token: 'skkpfNOJ6hHHnkOltCnNHzbwIvPrhcZVbG7wzlCijWRDTS7slNotUaNQqn3fo8ybnA4w00hZAiAGIWB7jAxcGsUNhsBzAREMQdh2AnzQzyhSYuRS1uDWJ5HpmGSkmE5VxH39ViSNZ6oWNV1F86h3f7e90tjdVhodjE3tSx138yC7dzZN7viT', // or leave blank to be anonymous user
  useCdn: false
})

const slugify = function(text) {

    if (!text) {
        return "";
    }
    return text
      .toString()
      .toLowerCase()
      .replace(/\s+/g, '-') // Replace spaces with -
      .replace(/[^\w-]+/g, '') // Remove all non-word chars
      .replace(/--+/g, '-') // Replace multiple - with single -
      .replace(/^-+/, '') // Trim - from start of text
      .replace(/-+$/, '') // Trim - from end of text
}

async function createPost(directory) {
  // Parse the mdx file
  const mdxPath = path.join(directory, 'index.mdx')
  const mdxData = fs.readFileSync(mdxPath, 'utf8')
  const { data, content } = grayMatter(mdxData)

  // Extract data from the frontmatter
  const { title, category, tags } = data

  // Upload the image and get the asset document
  const imagePath = path.join(directory, 'image.png')
  const imageAsset = await client.assets.upload('image', fs.createReadStream(imagePath))

  const currentDate = new Date();
  const formattedDate = currentDate.toISOString();

  // Create the post
  const post = {
    _type: 'post',
    title: title,
    slug: slugify(title),
    featureImg: {
      _type: 'image',
      asset: {
        _type: 'reference',
        _ref: imageAsset._id
      }
    },
    content: content,
    date: formattedDate,
    cate: category,
    tags: tags,
    frequency: 1,
  }

  await client.create(post)
}

// process.argv[2] is the directory path passed from the Python script
createPost(process.argv[2])