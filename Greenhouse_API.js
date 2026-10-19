async function getGreenhouseJob(boardToken, jobId) {
  const url =
    `https://boards-api.greenhouse.io/v1/boards/${encodeURIComponent(boardToken)}/jobs/${encodeURIComponent(jobId)}`;

  const response = await fetch(url);

  if (!response.ok) {
    if (response.status === 404) {
      throw new Error("Job not found. Check the board token and job ID.");
    }

    throw new Error(`Greenhouse API error: ${response.status}`);
  }

  const job = await response.json();

  return {
    id: job.id,
    title: job.title,
    location: job.location?.name ?? "Not specified",
    description: job.content ?? "",
    applicationUrl: job.absolute_url,
    updatedAt: job.updated_at,
    publishedAt: job.first_published ?? null
  };

  async function getGreenhouseJobs(boardToken) {
  const url =
    `https://boards-api.greenhouse.io/v1/boards/${encodeURIComponent(boardToken)}/jobs?content=true`;

  const response = await fetch(url);

  if (!response.ok) {
    throw new Error(`Request failed: ${response.status}`);
  }

  const data = await response.json();
  return data.jobs;
}
}
