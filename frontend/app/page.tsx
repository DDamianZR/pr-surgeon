export default function Home() {
  return (
    <main className="min-h-screen flex flex-col items-center justify-center bg-gradient-to-br from-white to-blue-50">
      <div className="max-w-4xl mx-auto px-6 text-center">
        <h1 className="text-6xl font-bold text-ibm-blue mb-4">
          PR Surgeon ⚕️
        </h1>
        <p className="text-2xl text-ibm-gray mb-8">
          Decompose monster Pull Requests into safe, reviewable sub-PRs
        </p>
        <p className="text-lg text-gray-600 mb-12 max-w-2xl mx-auto">
          Enterprise migrations produce 300+ file PRs that block engineering for weeks. 
          PR Surgeon uses repository-aware AI to produce a safe decomposition plan in seconds.
        </p>
        <button 
          className="bg-ibm-blue hover:bg-ibm-blue-dark text-white font-semibold py-4 px-8 rounded-lg text-lg transition-colors duration-200 shadow-lg hover:shadow-xl"
          disabled
        >
          Coming Soon
        </button>
        <div className="mt-16 text-sm text-gray-500">
          <p>Built with IBM Bob for the IBM Bob Hackathon 2026</p>
        </div>
      </div>
    </main>
  );
}

// Made with Bob
