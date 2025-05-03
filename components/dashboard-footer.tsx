import Link from "next/link"

export function DashboardFooter() {
  return (
    <footer className="border-t bg-white py-6">
      <div className="container mx-auto px-4">
        <div className="flex flex-wrap justify-center gap-x-6 gap-y-2 text-sm text-muted-foreground">
          <Link href="/docs" className="hover:underline hover:text-foreground">
            Documentation
          </Link>
          <Link href="/support" className="hover:underline hover:text-foreground">
            Support
          </Link>
          <Link href="/terms" className="hover:underline hover:text-foreground">
            Terms of Service
          </Link>
          <Link href="/privacy" className="hover:underline hover:text-foreground">
            Privacy Policy
          </Link>
        </div>
        <p className="mt-4 text-center text-xs text-muted-foreground">
          © {new Date().getFullYear()} ScrapeWizard. All rights reserved.
        </p>
      </div>
    </footer>
  )
}
